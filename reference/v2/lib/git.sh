#!/bin/bash
# Loop V2 Git Operations - Commit and safety functions
#
# Dependencies: lib/ui.sh (for print_status)
# Requires: SPRINT, SPRINT_DIR

auto_commit() {
    local message="$1"

    if git diff --quiet HEAD 2>/dev/null && git diff --staged --quiet 2>/dev/null; then
        print_status "info" "No changes to commit"
        return 0
    fi

    print_status "info" "Committing: $message"

    # Stage tracked files and new files in expected directories
    # Avoid staging sensitive files
    git add -u  # Stage modified tracked files

    # Stage new files in safe directories only
    git add "$SPRINT_DIR/" 2>/dev/null || true
    git add "src/" 2>/dev/null || true
    git add "frontend/src/" 2>/dev/null || true
    git add "app/" 2>/dev/null || true
    git add "lib/" 2>/dev/null || true
    git add "tests/" 2>/dev/null || true
    git add "test/" 2>/dev/null || true

    # Explicitly unstage sensitive files if accidentally added
    git reset HEAD -- "*.env*" ".env*" "*secret*" "*credential*" "*.pem" "*.key" 2>/dev/null || true

    # Final safety check
    if ! check_sensitive_files; then
        print_status "error" "Commit aborted due to sensitive files"
        return 1
    fi

    # Commit with message
    git commit -m "$message

Co-Authored-By: Loop-V2 <loop-v2@automated>" 2>/dev/null || true
}

atomic_task_commit() {
    local task_id="$1"
    local task_name="$2"

    auto_commit "loop-v2($SPRINT): Task $task_id - $task_name"
}

check_sensitive_files() {
    # Warn if sensitive files are staged
    local sensitive_staged=$(git diff --cached --name-only 2>/dev/null | grep -iE "\.env|secret|credential|\.pem|\.key|password" || true)

    if [[ -n "$sensitive_staged" ]]; then
        print_status "error" "SENSITIVE FILES STAGED - Aborting commit!"
        echo "$sensitive_staged"
        git reset HEAD -- $sensitive_staged 2>/dev/null || true
        return 1
    fi
    return 0
}

ensure_gitignore() {
    # Ensure .gitignore has common sensitive patterns
    if [[ -f ".gitignore" ]]; then
        local patterns=(".env" ".env.*" "*.pem" "*.key" "*secret*" "*credential*")
        for pattern in "${patterns[@]}"; do
            if ! grep -q "^${pattern}$" .gitignore 2>/dev/null; then
                print_status "warn" "Adding $pattern to .gitignore"
                echo "$pattern" >> .gitignore
            fi
        done
    fi
}
