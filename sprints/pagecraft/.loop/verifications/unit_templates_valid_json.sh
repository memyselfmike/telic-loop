#!/usr/bin/env bash
# Verification: All 3 template JSON files are valid and parseable
# PRD Reference: F1 Template Selection, Architecture - templates/
# Vision Goal: Template foundation
# Category: unit
set -euo pipefail

echo "=== Unit: Template JSON Files Valid ==="

cd "$(dirname "$0")/../.."

FAIL=0

for template in saas event portfolio; do
  TEMPLATE_FILE="public/templates/${template}.json"

  if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "FAIL: Template file $TEMPLATE_FILE does not exist"
    FAIL=1
    continue
  fi

  # Validate JSON syntax
  if ! python -m json.tool "$TEMPLATE_FILE" > /dev/null 2>&1; then
    echo "FAIL: $TEMPLATE_FILE is not valid JSON"
    FAIL=1
    continue
  fi

  # Check for required structure
  if ! python -c "
import json, sys
with open('$TEMPLATE_FILE', encoding='utf-8') as f:
    data = json.load(f)
    if 'name' not in data:
        print('Missing name field')
        sys.exit(1)
    if 'sections' not in data:
        print('Missing sections field')
        sys.exit(1)
    if not isinstance(data['sections'], list):
        print('sections must be an array')
        sys.exit(1)
    if len(data['sections']) != 5:
        print(f'Expected 5 sections, got {len(data[\"sections\"])}')
        sys.exit(1)
" 2>&1; then
    echo "FAIL: $TEMPLATE_FILE has invalid structure"
    FAIL=1
    continue
  fi

  echo "PASS: $TEMPLATE_FILE is valid"
done

if [[ $FAIL -eq 0 ]]; then
  echo "PASS: All 3 template JSON files are valid"
  exit 0
else
  exit 1
fi
