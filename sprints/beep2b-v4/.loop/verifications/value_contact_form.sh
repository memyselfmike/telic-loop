#!/bin/bash
# Value test: Contact form submits to CMS

set -e

echo "=== Contact Form Submission Test ==="

# Check contact page loads
echo "Testing contact page..."
CONTACT_HTML=$(curl -s http://localhost:4321/contact || echo "")

if ! echo "$CONTACT_HTML" | grep -q "contact-form"; then
  echo "FAIL: Contact form not found on page"
  exit 1
fi

echo "✓ Contact form renders"

# Check FormSubmissions collection exists in CMS
echo "Testing FormSubmissions API endpoint..."
FORM_SUBMISSIONS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/form-submissions || echo "000")

if [ "$FORM_SUBMISSIONS_RESPONSE" != "200" ]; then
  echo "FAIL: FormSubmissions API endpoint not responding (got $FORM_SUBMISSIONS_RESPONSE)"
  exit 1
fi

echo "✓ FormSubmissions collection accessible"

# Test form submission
echo "Testing form submission..."
TIMESTAMP=$(date +%s)
SUBMIT_RESPONSE=$(curl -s -X POST http://localhost:3000/api/form-submissions \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test User $TIMESTAMP\",\"email\":\"test$TIMESTAMP@example.com\",\"company\":\"Test Co\",\"message\":\"This is a test submission from verification script\"}" \
  -w "%{http_code}" -o /tmp/form_submit_response.txt 2>/dev/null || echo "000")

if [ "$SUBMIT_RESPONSE" != "200" ] && [ "$SUBMIT_RESPONSE" != "201" ]; then
  echo "FAIL: Form submission failed with status $SUBMIT_RESPONSE"
  if [ -f /tmp/form_submit_response.txt ]; then
    cat /tmp/form_submit_response.txt
  fi
  exit 1
fi

echo "✓ Form submission successful"

# Verify submission was stored
echo "Verifying submission in database..."
sleep 1  # Give DB a moment to index
SUBMISSIONS=$(curl -s http://localhost:3000/api/form-submissions || echo "")

if ! echo "$SUBMISSIONS" | grep -q "Test User"; then
  echo "FAIL: No submissions found in database"
  exit 1
fi

echo "✓ Submission stored in CMS database"

echo ""
echo "=== PASS: Contact form integration working ==="
exit 0
