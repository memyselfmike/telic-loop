#!/bin/bash
# Value test: CMS data flows to frontend

set -e

echo "=== CMS Data Flow Test ==="

# Test categories endpoint
echo "Testing categories API..."
CATEGORIES=$(curl -s http://localhost:3000/api/categories || echo "")
if [ -z "$CATEGORIES" ]; then
  echo "FAIL: Categories API returned empty"
  exit 1
fi

# Check if response contains "docs" and has data
if ! echo "$CATEGORIES" | grep -q '"docs"'; then
  echo "FAIL: Categories API response missing docs array"
  exit 1
fi

if ! echo "$CATEGORIES" | grep -q 'LinkedIn'; then
  echo "FAIL: Categories missing expected content"
  exit 1
fi

echo "✓ Categories API returns data"

# Test posts endpoint
echo "Testing posts API..."
POSTS=$(curl -s http://localhost:3000/api/posts || echo "")
if [ -z "$POSTS" ]; then
  echo "FAIL: Posts API returned empty"
  exit 1
fi

if ! echo "$POSTS" | grep -q '"docs"'; then
  echo "FAIL: Posts API response missing docs array"
  exit 1
fi

if ! echo "$POSTS" | grep -q 'LinkedIn'; then
  echo "FAIL: Posts missing expected content"
  exit 1
fi

echo "✓ Posts API returns seed data"

# Test testimonials endpoint
echo "Testing testimonials API..."
TESTIMONIALS=$(curl -s http://localhost:3000/api/testimonials || echo "")
if [ -z "$TESTIMONIALS" ]; then
  echo "FAIL: Testimonials API returned empty"
  exit 1
fi

if ! echo "$TESTIMONIALS" | grep -q 'Sarah M.'; then
  echo "FAIL: Testimonials missing expected content (Sarah M.)"
  exit 1
fi

echo "✓ Testimonials API returns seed data"

# Test that blog page shows posts from CMS
echo "Testing blog page CMS integration..."
BLOG_HTML=$(curl -s http://localhost:4321/blog || echo "")
if ! echo "$BLOG_HTML" | grep -q "LinkedIn"; then
  echo "FAIL: Blog page missing expected post titles from CMS"
  exit 1
fi
echo "✓ Blog page displays CMS content"

# Test that homepage shows testimonials
echo "Testing homepage testimonials..."
HOME_HTML=$(curl -s http://localhost:4321 || echo "")
if ! echo "$HOME_HTML" | grep -q "Sarah M."; then
  echo "FAIL: Homepage missing testimonial from Sarah M."
  exit 1
fi
echo "✓ Homepage displays testimonials from CMS"

echo ""
echo "=== PASS: CMS data flows correctly to frontend ==="
exit 0
