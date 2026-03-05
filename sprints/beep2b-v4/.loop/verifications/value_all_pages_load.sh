#!/bin/bash
# Value test: All 7 pages load with 200 status

set -e

echo "=== All Pages Load Test ==="

PAGES=(
  "/"
  "/how-it-works"
  "/services"
  "/about"
  "/contact"
  "/blog"
)

for page in "${PAGES[@]}"; do
  echo "Testing http://localhost:4321$page..."
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:4321$page" || echo "000")
  
  if [ "$STATUS" != "200" ]; then
    echo "FAIL: Page $page returned $STATUS, expected 200"
    exit 1
  fi
  
  echo "✓ $page loads successfully"
done

# Test a sample blog post (should be generated from seed data)
echo "Testing blog post page..."
BLOG_POST_HTML=$(curl -s "http://localhost:4321/blog/the-anatomy-of-a-high-converting-linkedin-profile" || echo "")
if [ -z "$BLOG_POST_HTML" ]; then
  echo "FAIL: Blog post page did not return HTML"
  exit 1
fi

if ! echo "$BLOG_POST_HTML" | grep -q "LinkedIn Profile"; then
  echo "FAIL: Blog post page missing expected content"
  exit 1
fi

echo "✓ Blog post page loads successfully"

echo ""
echo "=== PASS: All 7 pages load with content ==="
exit 0
