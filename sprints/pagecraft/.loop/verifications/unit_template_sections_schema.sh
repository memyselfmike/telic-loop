#!/usr/bin/env bash
# Verification: Each template has exactly 5 sections with correct types and schema
# PRD Reference: F2 Section Management - 5 section types (hero, features, testimonials, pricing, cta)
# Vision Goal: Template content structure
# Category: unit
set -euo pipefail

echo "=== Unit: Template Sections Match PRD Schema ==="

cd "$(dirname "$0")/../.."

FAIL=0

EXPECTED_TYPES=("hero" "features" "testimonials" "pricing" "cta")

for template in saas event portfolio; do
  TEMPLATE_FILE="public/templates/${template}.json"

  echo "Checking $template template..."

  # Verify each section has id, type, and content
  if ! python -c "
import json, sys
with open('$TEMPLATE_FILE', encoding='utf-8') as f:
    data = json.load(f)
    sections = data.get('sections', [])

    if len(sections) != 5:
        print(f'Expected 5 sections, got {len(sections)}')
        sys.exit(1)

    types_found = []
    for i, section in enumerate(sections):
        if 'id' not in section:
            print(f'Section {i} missing id field')
            sys.exit(1)
        if 'type' not in section:
            print(f'Section {i} missing type field')
            sys.exit(1)
        if 'content' not in section:
            print(f'Section {i} missing content field')
            sys.exit(1)
        if not isinstance(section['content'], dict):
            print(f'Section {i} content must be an object')
            sys.exit(1)
        types_found.append(section['type'])

    # Verify all 5 required types present
    expected = set(['hero', 'features', 'testimonials', 'pricing', 'cta'])
    actual = set(types_found)
    if expected != actual:
        print(f'Expected types {expected}, got {actual}')
        sys.exit(1)
" 2>&1; then
    echo "FAIL: $template template has invalid section structure"
    FAIL=1
    continue
  fi

  echo "PASS: $template template has valid section structure"
done

if [[ $FAIL -eq 0 ]]; then
  echo "PASS: All templates have correct section schema"
  exit 0
else
  exit 1
fi
