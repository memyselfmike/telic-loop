#!/bin/bash
# Loop V2 Bootstrap - Defines LOOP_ROOT for all sourced modules
#
# This must be sourced FIRST by loop.sh
# All other modules use $LOOP_ROOT instead of $SCRIPT_DIR

# Resolve the absolute path to the loop-v2 directory
# Works correctly whether sourced from loop.sh or run directly
LOOP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LOOP_ROOT
