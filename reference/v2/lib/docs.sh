#!/bin/bash
# Loop V2 Document Validation - Check required sprint documents
#
# Dependencies: lib/ui.sh (for print_status)
# Requires: VISION_FILE, PRD_FILE, ARCH_FILE

check_docs_exist() {
    local missing=0

    if [[ ! -f "$VISION_FILE" ]]; then
        print_status "error" "VISION.md not found: $VISION_FILE"
        missing=1
    else
        print_status "ok" "VISION.md found"
    fi

    if [[ ! -f "$PRD_FILE" ]]; then
        print_status "error" "PRD.md not found: $PRD_FILE"
        missing=1
    else
        print_status "ok" "PRD.md found"
    fi

    if [[ ! -f "$ARCH_FILE" ]]; then
        print_status "warn" "ARCHITECTURE.md not found (optional): $ARCH_FILE"
    else
        print_status "ok" "ARCHITECTURE.md found"
    fi

    return $missing
}
