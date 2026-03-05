#!/bin/bash
# Value: All 7 pages load successfully

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Verifying All 7 Pages Load ==="

PAGES=(
  "/"
  "/how-it-works"
  "/services"
  "/about"
  "/blog"
  "/contact"
  "/blog/the-anatomy-of-a-high-converting-linkedin-profile"
)

PAGE_NAMES=(
  "Home"
  "How It Works"
  "Services"
  "About"
  "Blog"
  "Contact"
  "Blog Post"
)

for i in "${!PAGES[@]}"; do
  PAGE="${PAGES[$i]}"
  NAME="${PAGE_NAMES[$i]}"

  echo "Testing $NAME ($PAGE)..."
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:4321$PAGE" || echo "000")

  if [ "$STATUS" != "200" ]; then
    echo "FAIL: $NAME returned HTTP $STATUS"
    exit 1
  fi

  echo "✓ $NAME loads successfully"
done

echo "=== All Pages Verification PASSED ==="
exit 0
