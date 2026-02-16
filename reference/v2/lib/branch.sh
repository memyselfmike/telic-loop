#!/bin/bash
# Loop V2 Branch Management - Branch creation and switching
#
# Dependencies: lib/config.sh (for PROTECTED_BRANCHES), lib/ui.sh (for print_status)
# Requires: SPRINT

# Check if a branch is protected
is_protected_branch() {
    local branch="$1"
    for protected in $PROTECTED_BRANCHES; do
        if [[ "$branch" == "$protected" ]]; then
            return 0
        fi
    done
    return 1
}

# Setup the working branch for this sprint
# Sets BRANCH_NAME as a side effect
setup_sprint_branch() {
    local current_branch=$(git branch --show-current)

    # Stash any uncommitted changes if on protected branch
    if is_protected_branch "$current_branch"; then
        if ! git diff --quiet HEAD 2>/dev/null || ! git diff --staged --quiet 2>/dev/null; then
            print_status "warn" "Uncommitted changes on $current_branch - stashing"
            git stash push -m "loop-v2-auto-stash-$(date +%s)"
        fi
    fi

    if [[ "$current_branch" == loop-v2/${SPRINT}-* ]]; then
        BRANCH_NAME="$current_branch"
        print_status "ok" "Already on sprint branch: $BRANCH_NAME"
    else
        # Check for existing branch
        local existing_branch=$(git branch --list "loop-v2/${SPRINT}-*" | head -1 | sed 's/^[* ]*//')

        if [[ -n "$existing_branch" ]]; then
            BRANCH_NAME="$existing_branch"
            print_status "info" "Switching to existing branch: $BRANCH_NAME"
            git checkout "$BRANCH_NAME"
        else
            # Create new branch from current HEAD
            local timestamp=$(date '+%Y%m%d-%H%M%S')
            BRANCH_NAME="loop-v2/${SPRINT}-${timestamp}"

            if is_protected_branch "$current_branch"; then
                print_status "info" "Creating branch from $current_branch: $BRANCH_NAME"
            else
                print_status "info" "Creating branch: $BRANCH_NAME"
            fi

            git checkout -b "$BRANCH_NAME"
        fi
    fi

    # Verify we're not on a protected branch before proceeding
    if is_protected_branch "$(git branch --show-current)"; then
        print_status "error" "Still on protected branch! Cannot proceed."
        exit 1
    fi

    print_status "ok" "Working on branch: $BRANCH_NAME"
    export BRANCH_NAME
}
