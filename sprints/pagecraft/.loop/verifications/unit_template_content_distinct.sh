#!/usr/bin/env bash
# Verification: SaaS/Event/Portfolio templates have meaningfully different content
# PRD Reference: Task 1.1 - Content must be distinct per template
# Vision Goal: Professional, template-specific content
# Category: unit
set -euo pipefail

echo "=== Unit: Template Content is Distinct ==="

cd "$(dirname "$0")/../.."

# Extract all text content from each template and compare
SAAS_CONTENT=$(python -c "
import json
with open('public/templates/saas.json', encoding='utf-8') as f:
    data = json.load(f)
    print(json.dumps(data))
" | grep -oE '"[^"]{10,}"' | sort)

EVENT_CONTENT=$(python -c "
import json
with open('public/templates/event.json', encoding='utf-8') as f:
    data = json.load(f)
    print(json.dumps(data))
" | grep -oE '"[^"]{10,}"' | sort)

PORTFOLIO_CONTENT=$(python -c "
import json
with open('public/templates/portfolio.json', encoding='utf-8') as f:
    data = json.load(f)
    print(json.dumps(data))
" | grep -oE '"[^"]{10,}"' | sort)

# Calculate similarity by counting shared strings
SAAS_EVENT_SHARED=$(comm -12 <(echo "$SAAS_CONTENT") <(echo "$EVENT_CONTENT") | wc -l)
SAAS_PORTFOLIO_SHARED=$(comm -12 <(echo "$SAAS_CONTENT") <(echo "$PORTFOLIO_CONTENT") | wc -l)
EVENT_PORTFOLIO_SHARED=$(comm -12 <(echo "$EVENT_CONTENT") <(echo "$PORTFOLIO_CONTENT") | wc -l)

SAAS_TOTAL=$(echo "$SAAS_CONTENT" | wc -l)

# Calculate similarity percentage
SAAS_EVENT_SIMILARITY=$((SAAS_EVENT_SHARED * 100 / SAAS_TOTAL))
SAAS_PORTFOLIO_SIMILARITY=$((SAAS_PORTFOLIO_SHARED * 100 / SAAS_TOTAL))
EVENT_PORTFOLIO_SIMILARITY=$((EVENT_PORTFOLIO_SHARED * 100 / SAAS_TOTAL))

echo "Content similarity: SaaS-Event: $SAAS_EVENT_SIMILARITY%, SaaS-Portfolio: $SAAS_PORTFOLIO_SIMILARITY%, Event-Portfolio: $EVENT_PORTFOLIO_SIMILARITY%"

# Templates should be less than 30% similar (allow some overlap for structural text like "Features", "Pricing")
if [[ $SAAS_EVENT_SIMILARITY -lt 30 && $SAAS_PORTFOLIO_SIMILARITY -lt 30 && $EVENT_PORTFOLIO_SIMILARITY -lt 30 ]]; then
  echo "PASS: Templates have distinct content (< 30% similarity)"
  exit 0
else
  echo "FAIL: Templates are too similar (>= 30% shared content). Templates should have unique, template-specific text."
  exit 1
fi
