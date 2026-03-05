#!/bin/bash
# Integration: CMS has seed data (posts, categories, testimonials)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Verifying CMS Seed Data ==="

# Check categories (expect 9)
echo "Checking categories..."
CATEGORIES_RESPONSE=$(curl -s http://localhost:3000/api/categories)
CATEGORIES_COUNT=$(echo "$CATEGORIES_RESPONSE" | grep -o '"totalDocs":[0-9]*' | grep -o '[0-9]*' || echo "0")

if [ "$CATEGORIES_COUNT" -lt 9 ]; then
  echo "FAIL: Expected at least 9 categories, found $CATEGORIES_COUNT"
  exit 1
fi

echo "✓ Categories seeded ($CATEGORIES_COUNT categories)"

# Check posts (expect 3)
echo "Checking posts..."
POSTS_RESPONSE=$(curl -s http://localhost:3000/api/posts)
POSTS_COUNT=$(echo "$POSTS_RESPONSE" | grep -o '"totalDocs":[0-9]*' | grep -o '[0-9]*' || echo "0")

if [ "$POSTS_COUNT" -lt 3 ]; then
  echo "FAIL: Expected at least 3 posts, found $POSTS_COUNT"
  exit 1
fi

echo "✓ Posts seeded ($POSTS_COUNT posts)"

# Check testimonials (expect 3)
echo "Checking testimonials..."
TESTIMONIALS_RESPONSE=$(curl -s http://localhost:3000/api/testimonials)
TESTIMONIALS_COUNT=$(echo "$TESTIMONIALS_RESPONSE" | grep -o '"totalDocs":[0-9]*' | grep -o '[0-9]*' || echo "0")

if [ "$TESTIMONIALS_COUNT" -lt 3 ]; then
  echo "FAIL: Expected at least 3 testimonials, found $TESTIMONIALS_COUNT"
  exit 1
fi

echo "✓ Testimonials seeded ($TESTIMONIALS_COUNT testimonials)"

# Verify specific testimonial content
echo "Checking testimonial content..."
if ! echo "$TESTIMONIALS_RESPONSE" | grep -q "Sarah M."; then
  echo "FAIL: Missing Sarah M. testimonial"
  exit 1
fi

echo "✓ Testimonial content verified"

echo "=== CMS Seed Data Verification PASSED ==="
exit 0
