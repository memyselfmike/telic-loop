#!/bin/bash
# Value: Pages contain expected content from PRD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Verifying Page Content ==="

# Home page
echo "Checking Home page content..."
HOME_CONTENT=$(curl -s http://localhost:4321/)

if ! echo "$HOME_CONTENT" | grep -q "Consistent B2B Leads From LinkedIn"; then
  echo "FAIL: Home page missing hero headline"
  exit 1
fi

if ! echo "$HOME_CONTENT" | grep -q "500+"; then
  echo "FAIL: Home page missing stats"
  exit 1
fi

echo "✓ Home page content verified"

# About page
echo "Checking About page content..."
ABOUT_CONTENT=$(curl -s http://localhost:4321/about)

if ! echo "$ABOUT_CONTENT" | grep -q "Building B2B Lead Generation"; then
  echo "FAIL: About page missing title"
  exit 1
fi

if ! echo "$ABOUT_CONTENT" | grep -q "Relationships Over Reach"; then
  echo "FAIL: About page missing values"
  exit 1
fi

echo "✓ About page content verified"

# How It Works page
echo "Checking How It Works page..."
WORKS_CONTENT=$(curl -s http://localhost:4321/how-it-works)

if ! echo "$WORKS_CONTENT" | grep -q "Build.*Engage.*Educate.*Promote"; then
  echo "FAIL: How It Works page missing BEEP steps"
  exit 1
fi

echo "✓ How It Works page content verified"

# Services page
echo "Checking Services page..."
SERVICES_CONTENT=$(curl -s http://localhost:4321/services)

if ! echo "$SERVICES_CONTENT" | grep -q "LinkedIn Marketing"; then
  echo "FAIL: Services page missing service 1"
  exit 1
fi

if ! echo "$SERVICES_CONTENT" | grep -q "Thought Leadership Marketing"; then
  echo "FAIL: Services page missing service 2"
  exit 1
fi

if ! echo "$SERVICES_CONTENT" | grep -q "LinkedIn Training"; then
  echo "FAIL: Services page missing service 3"
  exit 1
fi

echo "✓ Services page content verified"

# Contact page
echo "Checking Contact page..."
CONTACT_CONTENT=$(curl -s http://localhost:4321/contact)

if ! echo "$CONTACT_CONTENT" | grep -q "Discovery Call"; then
  echo "FAIL: Contact page missing discovery call heading"
  exit 1
fi

if ! echo "$CONTACT_CONTENT" | grep -q "hello@beep2b.com"; then
  echo "FAIL: Contact page missing email"
  exit 1
fi

echo "✓ Contact page content verified"

# Blog page
echo "Checking Blog page..."
BLOG_CONTENT=$(curl -s http://localhost:4321/blog)

if ! echo "$BLOG_CONTENT" | grep -q "The Beep2B Blog"; then
  echo "FAIL: Blog page missing title"
  exit 1
fi

if ! echo "$BLOG_CONTENT" | grep -q "Filter by category"; then
  echo "FAIL: Blog page missing category filter"
  exit 1
fi

echo "✓ Blog page content verified"

# Blog post page
echo "Checking Blog post page..."
POST_CONTENT=$(curl -s http://localhost:4321/blog/the-anatomy-of-a-high-converting-linkedin-profile)

if ! echo "$POST_CONTENT" | grep -q "The Anatomy of a High-Converting LinkedIn Profile"; then
  echo "FAIL: Blog post page missing title"
  exit 1
fi

if ! echo "$POST_CONTENT" | grep -q "Your LinkedIn profile is your digital storefront"; then
  echo "FAIL: Blog post page missing excerpt"
  exit 1
fi

echo "✓ Blog post page content verified"

echo "=== Page Content Verification PASSED ==="
exit 0
