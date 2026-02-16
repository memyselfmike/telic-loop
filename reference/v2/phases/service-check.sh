#!/bin/bash
# Loop V2 Service Check Phase - Service readiness verification
#
# Dependencies: lib/services.sh, lib/state.sh, lib/ui.sh, lib/prompts.sh, lib/git.sh
# Requires: ITERATION
#
# DESIGN PRINCIPLE: Service readiness should NOT block implementation.
# For greenfield projects, implementation is what CREATES the services.
# We check readiness, create tasks if needed, and PROCEED.

# Track service check attempts to prevent infinite loops
SERVICE_CHECK_ATTEMPTS=${SERVICE_CHECK_ATTEMPTS:-0}
MAX_SERVICE_CHECK_ATTEMPTS=3

# Check if all required services are actually running
all_services_running() {
    local all_running=true

    if vision_requires_backend; then
        if ! curl -s http://localhost:${LOOP_BACKEND_PORT}${LOOP_BACKEND_HEALTH} > /dev/null 2>&1; then
            all_running=false
        fi
    fi

    if vision_requires_frontend; then
        if ! curl -s http://localhost:${LOOP_FRONTEND_PORT} > /dev/null 2>&1; then
            all_running=false
        fi
    fi

    if vision_requires_browser; then
        if ! curl -s http://localhost:${LOOP_CDP_PORT}/json/version > /dev/null 2>&1; then
            # Browser is optional - don't block on it
            print_status "warn" "Chrome CDP not running (browser automation limited)"
        fi
    fi

    $all_running
}

# Check if service implementation exists (not just running)
# This helps distinguish "not implemented yet" from "broken startup"
service_implementation_exists() {
    local service_type="$1"

    case "$service_type" in
        backend|api)
            # Check for common backend entry points
            [[ -f "src/server.ts" ]] || [[ -f "src/server.js" ]] || \
            [[ -f "src/api/server.ts" ]] || [[ -f "src/api/server.js" ]] || \
            [[ -f "src/app.ts" ]] || [[ -f "src/app.js" ]] || \
            [[ -f "server.ts" ]] || [[ -f "server.js" ]] || \
            [[ -f "app.py" ]] || [[ -f "main.py" ]] || \
            [[ -f "cmd/server/main.go" ]] || [[ -f "main.go" ]]
            ;;
        frontend)
            # Check for common frontend indicators
            [[ -d "frontend" ]] || [[ -d "client" ]] || [[ -d "web" ]] || \
            [[ -f "src/app/page.tsx" ]] || [[ -f "src/app/page.jsx" ]] || \
            [[ -f "src/pages/index.tsx" ]] || [[ -f "src/pages/index.jsx" ]] || \
            [[ -f "src/App.tsx" ]] || [[ -f "src/App.jsx" ]] || \
            [[ -f "index.html" ]]
            ;;
        browser)
            # Browser automation typically requires scripts
            [[ -f "package.json" ]] && grep -qE "puppeteer|playwright|selenium" package.json 2>/dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

run_service_check_phase() {
    if ! gate_passed "service_readiness"; then
        # Increment attempt counter (use || true to prevent set -e exit when counter is 0)
        ((SERVICE_CHECK_ATTEMPTS++)) || true
        export SERVICE_CHECK_ATTEMPTS

        print_status "info" "Service check attempt $SERVICE_CHECK_ATTEMPTS of $MAX_SERVICE_CHECK_ATTEMPTS"

        # Run the service readiness check (sets SERVICES_NEED_FIX)
        run_service_readiness_check

        # If there are services that need fix tasks, create and implement them
        if [[ ${#SERVICES_NEED_FIX[@]} -gt 0 ]]; then
            echo ""
            print_status "warn" "Found ${#SERVICES_NEED_FIX[@]} service(s) that should auto-start but don't"

            # Check if this is greenfield (services not implemented yet) vs brownfield (broken startup)
            local greenfield_services=()
            local brownfield_services=()

            for service in "${SERVICES_NEED_FIX[@]}"; do
                local service_type=$(echo "$service" | tr '[:upper:]' '[:lower:]' | awk '{print $1}')
                if service_implementation_exists "$service_type"; then
                    brownfield_services+=("$service")
                else
                    greenfield_services+=("$service")
                fi
            done

            if [[ ${#greenfield_services[@]} -gt 0 ]]; then
                print_status "info" "Greenfield detected: ${#greenfield_services[@]} service(s) not yet implemented"
                print_status "info" "These will be created during implementation phase"
            fi

            if [[ ${#brownfield_services[@]} -gt 0 ]]; then
                print_status "warn" "Brownfield: ${#brownfield_services[@]} service(s) exist but won't start"
                print_status "info" "Creating fix tasks..."
            fi

            # Create tasks for services that need fixes
            for service in "${SERVICES_NEED_FIX[@]}"; do
                create_service_startup_task "$service"
            done

            echo ""
            print_status "info" "Step 1: Analyzing service startup requirements..."
            run_prompt "service-readiness"

            auto_commit "loop-v2($SPRINT): Service readiness - created startup fix tasks"

            # Only attempt fixes on brownfield (existing but broken) services
            # For greenfield, let the implementation phase handle it
            if [[ ${#brownfield_services[@]} -gt 0 ]]; then
                echo ""
                print_status "info" "Step 2: Attempting to fix existing service startup..."
                run_prompt "implement"
                auto_commit "loop-v2($SPRINT): Service readiness - implemented startup fixes"

                # Retry service startup
                echo ""
                print_status "info" "Step 3: Retrying service startup after fixes..."
                start_required_services
            fi
        fi

        # Decision point: proceed or block?
        if all_services_running; then
            print_status "ok" "All required services are running"
            mark_gate_passed "service_readiness"
            SERVICE_CHECK_ATTEMPTS=0
            save_state "1" "$ITERATION"
        elif [[ $SERVICE_CHECK_ATTEMPTS -ge $MAX_SERVICE_CHECK_ATTEMPTS ]]; then
            # Max attempts reached - proceed anyway
            # This prevents infinite loops in greenfield or truly broken scenarios
            echo ""
            print_status "warn" "Max service check attempts ($MAX_SERVICE_CHECK_ATTEMPTS) reached"
            print_status "info" "Proceeding to implementation - services may be created/fixed there"
            print_status "info" "Implementation tasks have been created for missing services"
            echo ""

            # Mark gate as "deferred" - we'll re-check after implementation
            mark_gate_passed "service_readiness"
            SERVICE_CHECK_ATTEMPTS=0
            save_state "1" "$ITERATION"
        else
            print_status "info" "Services not ready - will retry (attempt $SERVICE_CHECK_ATTEMPTS/$MAX_SERVICE_CHECK_ATTEMPTS)"
            save_state "1" "$ITERATION"
        fi
    else
        # Gate passed but verify services are still running
        if ! all_services_running; then
            print_status "warn" "Services stopped - re-running service check"
            # Unmark the gate so we re-check
            STATE_GATES_PASSED=$(echo "$STATE_GATES_PASSED" | sed 's/service_readiness,//g')
            SERVICE_CHECK_ATTEMPTS=0
            save_state "1" "$ITERATION"
            # Return 1 to signal main loop should restart
            return 1
        else
            print_status "skip" "Service readiness already verified"
        fi
    fi
    return 0
}
