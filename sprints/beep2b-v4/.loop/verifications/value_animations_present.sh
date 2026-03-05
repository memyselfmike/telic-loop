#!/bin/bash
# Value test: Scroll animations are present in HTML

set -e

echo "=== Scroll Animations Test ==="

# Check homepage for animation attributes
echo "Testing homepage animations..."
HOME_HTML=$(curl -s http://localhost:4321 || echo "")

if ! echo "$HOME_HTML" | grep -q 'data-animate'; then
  echo "FAIL: Homepage missing data-animate attributes"
  exit 1
fi

if ! echo "$HOME_HTML" | grep -q 'data-stagger'; then
  echo "FAIL: Homepage missing data-stagger attributes"
  exit 1
fi

if ! echo "$HOME_HTML" | grep -q 'data-counter'; then
  echo "FAIL: Homepage missing data-counter attributes for trust bar"
  exit 1
fi

echo "✓ Homepage has scroll-triggered animations"

# Check animations CSS is included
if ! echo "$HOME_HTML" | grep -qi 'animations\.css'; then
  echo "FAIL: animations.css not included"
  exit 1
fi

echo "✓ Animation styles loaded"

# Check How It Works page has BEEP step animations
echo "Testing How It Works page animations..."
HIW_HTML=$(curl -s http://localhost:4321/how-it-works || echo "")

# Count steps by looking for step numbers 01, 02, 03, 04
STEP_COUNT=0
for num in "01" "02" "03" "04"; do
  if echo "$HIW_HTML" | grep -q "step-number.*>$num<"; then
    STEP_COUNT=$((STEP_COUNT + 1))
  fi
done

if [ "$STEP_COUNT" -lt 4 ]; then
  echo "FAIL: Expected 4 BEEP steps, found $STEP_COUNT"
  exit 1
fi

echo "✓ All 4 BEEP steps present with animations"

echo ""
echo "=== PASS: Scroll animations configured correctly ==="
exit 0
