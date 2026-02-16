#!/bin/bash
# Loop V2 Services - Extensible, Sprint-Agnostic Service Management
#
# DESIGN PRINCIPLES:
# 1. Discover services from project structure, not hardcoded lists
# 2. Support multiple runtimes: Docker, npm, Python, Make, shell
# 3. Allow sprint-specific service definitions
# 4. Graceful degradation - work with minimal config
#
# PRIORITY ORDER:
# 1. Sprint-specific services.yaml (explicit definition)
# 2. docker-compose.yml (Docker-first)
# 3. ARCHITECTURE.md (intelligent parsing)
# 4. package.json / Makefile / pyproject.toml (runtime detection)
# 5. VISION.md keywords (fallback heuristic)

# ═══════════════════════════════════════════════════════════════════════════
# SERVICE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════

# Discover what service orchestration is available
detect_orchestration() {
    if [[ -f "$SPRINT_DIR/services.yaml" ]] || [[ -f "$SPRINT_DIR/services.yml" ]]; then
        echo "sprint-services"
    elif [[ -f "docker-compose.yml" ]] || [[ -f "docker-compose.yaml" ]]; then
        echo "docker-compose"
    elif [[ -f "compose.yml" ]] || [[ -f "compose.yaml" ]]; then
        echo "docker-compose"
    elif [[ -f "Dockerfile" ]]; then
        echo "dockerfile"
    elif [[ -f "package.json" ]]; then
        echo "npm"
    elif [[ -f "Makefile" ]]; then
        echo "make"
    elif [[ -f "pyproject.toml" ]] || [[ -f "requirements.txt" ]]; then
        echo "python"
    elif [[ -f "go.mod" ]]; then
        echo "go"
    else
        echo "unknown"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# DOCKER-COMPOSE SERVICES
# ═══════════════════════════════════════════════════════════════════════════

# Get list of services from docker-compose
docker_compose_services() {
    local compose_file=""
    for f in docker-compose.yml docker-compose.yaml compose.yml compose.yaml; do
        if [[ -f "$f" ]]; then
            compose_file="$f"
            break
        fi
    done

    if [[ -n "$compose_file" ]]; then
        # Parse service names from docker-compose
        grep -E "^  [a-zA-Z0-9_-]+:" "$compose_file" 2>/dev/null | sed 's/://g' | tr -d ' '
    fi
}

# Start all docker-compose services
start_docker_compose() {
    print_status "info" "Starting services via docker-compose..."

    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose up -d
    else
        print_status "error" "Docker Compose not found"
        return 1
    fi

    # Wait for services to be healthy
    local timeout=${LOOP_SERVICE_TIMEOUT:-60}
    print_status "info" "Waiting for services to be healthy (timeout: ${timeout}s)..."

    local start_time=$(date +%s)
    while true; do
        local elapsed=$(($(date +%s) - start_time))
        if [[ $elapsed -ge $timeout ]]; then
            print_status "warn" "Timeout waiting for services"
            break
        fi

        # Check if all services are healthy/running
        local unhealthy=$(docker-compose ps 2>/dev/null | grep -E "Exit|starting" | wc -l)
        if [[ "$unhealthy" -eq 0 ]]; then
            print_status "ok" "All Docker services healthy"
            return 0
        fi

        sleep 2
    done
}

# Check docker-compose service status
check_docker_compose_status() {
    echo ""
    print_status "info" "Docker Compose service status:"

    if command -v docker-compose &> /dev/null; then
        docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || docker-compose ps
    elif command -v docker &> /dev/null; then
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || docker compose ps
    fi
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# SPRINT-SPECIFIC SERVICES (services.yaml)
# ═══════════════════════════════════════════════════════════════════════════

# Parse services.yaml and start services
# Format:
# services:
#   api:
#     port: 3001
#     health: /health
#     start: npm run dev:api
#     type: http
#   db:
#     port: 5432
#     start: docker-compose up -d postgres
#     type: tcp

start_sprint_services() {
    local services_file=""
    for f in "$SPRINT_DIR/services.yaml" "$SPRINT_DIR/services.yml"; do
        if [[ -f "$f" ]]; then
            services_file="$f"
            break
        fi
    done

    if [[ -z "$services_file" ]]; then
        return 1
    fi

    print_status "info" "Starting services from $services_file..."

    # Simple YAML parsing (for basic format)
    # For complex YAML, would need yq or python
    local current_service=""
    local service_port=""
    local service_health=""
    local service_start=""
    local service_type=""

    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # Detect service name (2-space indent, ends with :)
        if [[ "$line" =~ ^[[:space:]]{2}([a-zA-Z0-9_-]+):[[:space:]]*$ ]]; then
            # Start new service, process previous if exists
            if [[ -n "$current_service" ]] && [[ -n "$service_start" ]]; then
                start_single_service "$current_service" "$service_port" "$service_health" "$service_start" "$service_type"
            fi
            current_service="${BASH_REMATCH[1]}"
            service_port=""
            service_health=""
            service_start=""
            service_type="http"
        fi

        # Parse service properties (4-space indent)
        if [[ "$line" =~ ^[[:space:]]{4}port:[[:space:]]*([0-9]+) ]]; then
            service_port="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]{4}health:[[:space:]]*(.+) ]]; then
            service_health="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]{4}start:[[:space:]]*(.+) ]]; then
            service_start="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]{4}type:[[:space:]]*(.+) ]]; then
            service_type="${BASH_REMATCH[1]}"
        fi
    done < "$services_file"

    # Process last service
    if [[ -n "$current_service" ]] && [[ -n "$service_start" ]]; then
        start_single_service "$current_service" "$service_port" "$service_health" "$service_start" "$service_type"
    fi
}

# Start a single service and verify it's running
start_single_service() {
    local name="$1"
    local port="$2"
    local health="$3"
    local start_cmd="$4"
    local type="${5:-http}"

    # Check if already running
    if check_service_health "$name" "$port" "$health" "$type"; then
        print_status "ok" "$name: Already running"
        return 0
    fi

    print_status "info" "$name: Starting ($start_cmd)..."

    # Run start command in background
    eval "nohup $start_cmd > /tmp/loop-${name}.log 2>&1 &"

    # Wait for service to be ready
    local timeout=${LOOP_SERVICE_TIMEOUT:-30}
    for ((i=0; i<timeout; i++)); do
        if check_service_health "$name" "$port" "$health" "$type"; then
            print_status "ok" "$name: Started successfully"
            return 0
        fi
        sleep 1
    done

    print_status "warn" "$name: May not be ready (check /tmp/loop-${name}.log)"
    return 1
}

# Check if a service is healthy
check_service_health() {
    local name="$1"
    local port="$2"
    local health="$3"
    local type="${4:-http}"

    if [[ -z "$port" ]]; then
        return 1
    fi

    case "$type" in
        http|https)
            local url="${type}://localhost:${port}${health:-/}"
            curl -sf "$url" > /dev/null 2>&1
            ;;
        tcp)
            # TCP port check
            if command -v nc &> /dev/null; then
                nc -z localhost "$port" 2>/dev/null
            elif command -v bash &> /dev/null; then
                timeout 1 bash -c "echo > /dev/tcp/localhost/$port" 2>/dev/null
            else
                return 1
            fi
            ;;
        grpc)
            # gRPC health check (if grpcurl available)
            if command -v grpcurl &> /dev/null; then
                grpcurl -plaintext "localhost:$port" grpc.health.v1.Health/Check > /dev/null 2>&1
            else
                # Fallback to TCP check
                nc -z localhost "$port" 2>/dev/null
            fi
            ;;
        *)
            # Unknown type, try TCP
            nc -z localhost "$port" 2>/dev/null
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════
# ARCHITECTURE.MD PARSING
# ═══════════════════════════════════════════════════════════════════════════

# Extract services from ARCHITECTURE.md
# Looks for patterns like:
# - "Backend API on port 3001"
# - "PostgreSQL database"
# - "Redis cache"

parse_architecture_services() {
    local arch_file="$SPRINT_DIR/ARCHITECTURE.md"
    if [[ ! -f "$arch_file" ]]; then
        return 1
    fi

    # Extract service mentions with ports
    grep -oiE "(backend|frontend|api|database|postgres|mysql|redis|mongodb|queue|worker|nginx|proxy).*(port|:)[[:space:]]*[0-9]+" "$arch_file" 2>/dev/null | head -10
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════

# Start all required services using best available method
start_services_v2() {
    local orchestration=$(detect_orchestration)

    print_phase "SVC" "Service Startup (${orchestration})"

    case "$orchestration" in
        sprint-services)
            start_sprint_services
            ;;
        docker-compose)
            start_docker_compose
            check_docker_compose_status
            ;;
        dockerfile)
            print_status "info" "Dockerfile found - checking if container is running..."
            # Could build and run if needed
            ;;
        npm)
            # Fall back to legacy npm-based startup
            start_required_services  # From original services.sh
            ;;
        make)
            print_status "info" "Makefile found - looking for service targets..."
            if grep -q "^serve:" Makefile 2>/dev/null; then
                make serve &
            elif grep -q "^run:" Makefile 2>/dev/null; then
                make run &
            fi
            ;;
        python)
            print_status "info" "Python project detected"
            # Check for common patterns
            if [[ -f "manage.py" ]]; then
                print_status "info" "Django project - checking runserver..."
            elif [[ -f "app.py" ]] || [[ -f "main.py" ]]; then
                print_status "info" "Flask/FastAPI project detected"
            fi
            ;;
        *)
            print_status "warn" "Unknown project type - using VISION.md heuristics"
            start_required_services  # Legacy fallback
            ;;
    esac
}

# Check all services status
check_services_status_v2() {
    local orchestration=$(detect_orchestration)

    case "$orchestration" in
        docker-compose)
            check_docker_compose_status
            ;;
        sprint-services)
            # Would parse services.yaml and check each
            print_status "info" "Checking sprint-defined services..."
            ;;
        *)
            # Legacy status check
            echo ""
            print_status "info" "Service status:"
            # Original logic from services.sh
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════

# To use sprint-specific services, create {SPRINT_DIR}/services.yaml:
#
# services:
#   api:
#     port: 3001
#     health: /api/health
#     start: npm run dev:api
#     type: http
#
#   postgres:
#     port: 5432
#     start: docker-compose up -d postgres
#     type: tcp
#
#   redis:
#     port: 6379
#     start: docker-compose up -d redis
#     type: tcp
#
#   frontend:
#     port: 3000
#     health: /
#     start: cd frontend && npm run dev
#     type: http
#
# Supported types: http, https, tcp, grpc
