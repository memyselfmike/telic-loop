#!/bin/bash
# Loop V2 Prompt Execution - Run Claude prompts with retry logic
#
# Dependencies: lib/ui.sh (for print_status)
# Requires: LOOP_ROOT, SPRINT, SPRINT_DIR

run_prompt() {
    local prompt_name="$1"
    local prompt_file="$LOOP_ROOT/prompts/$prompt_name.md"
    local max_retries=3
    local retry_delay=5

    if [[ ! -f "$prompt_file" ]]; then
        print_status "error" "Prompt not found: $prompt_file"
        return 1
    fi

    # Substitute variables in prompt
    local temp_prompt=$(mktemp)
    sed "s|{SPRINT}|$SPRINT|g; s|{SPRINT_DIR}|$SPRINT_DIR|g" "$prompt_file" > "$temp_prompt"

    # Run Claude non-interactively with tool access
    # -p = non-interactive (print) mode, required for scripting
    # --allowedTools = explicitly enable tools (required with -p)
    # --dangerously-skip-permissions = bypass permission prompts
    local attempt=1
    while [[ $attempt -le $max_retries ]]; do
        if claude -p "$(<"$temp_prompt")" \
            --allowedTools "Bash,Read,Edit,Write,Glob,Grep" \
            --dangerously-skip-permissions 2>&1; then
            rm -f "$temp_prompt"
            return 0
        fi

        local exit_code=$?
        if [[ $attempt -lt $max_retries ]]; then
            print_status "warn" "Claude failed (attempt $attempt/$max_retries). Retrying in ${retry_delay}s..."
            sleep $retry_delay
            retry_delay=$((retry_delay * 2))  # Exponential backoff
        else
            print_status "error" "Claude failed after $max_retries attempts"
        fi
        ((attempt++))
    done

    rm -f "$temp_prompt"
    return 1
}
