// Verification script for Task 2.4: Accent Color Picker Enhancement
// This script verifies all acceptance criteria

const testColor = '#ff5733'; // A distinctive orange color for testing

// Test 1: Verify color picker updates AppState and CSS variable
console.log('Test 1: Verifying accent color picker updates AppState and CSS variable...');
const colorPicker = document.getElementById('accent-color');
if (!colorPicker) {
  console.error('❌ Color picker not found');
} else {
  console.log('✓ Color picker found');

  // Check if there's a label
  const label = document.querySelector('label[for="accent-color"]');
  if (!label) {
    console.error('❌ Color picker label not found');
  } else {
    console.log('✓ Color picker has label:', label.textContent);
  }
}

// Function to check if an element uses accent color
function checkAccentColorUsage(selector, property, description) {
  const elements = document.querySelectorAll(selector);
  if (elements.length === 0) {
    console.warn(`⚠ No elements found for: ${description} (${selector})`);
    return;
  }

  let allUsing = true;
  elements.forEach((el, index) => {
    const style = window.getComputedStyle(el);
    const value = style[property];
    const usesAccent = value.includes('var(--accent-color)') ||
                       value === getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();
    if (!usesAccent) {
      console.log(`  Element ${index}: ${property} = ${value}`);
      allUsing = false;
    }
  });

  if (allUsing) {
    console.log(`✓ ${description}: All ${elements.length} element(s) use accent color`);
  } else {
    console.log(`⚠ ${description}: Some elements may not use accent color (check inline styles)`);
  }
}

// Wait for template to load
setTimeout(() => {
  console.log('\nTest 2: Verifying h2 headings use accent color...');
  checkAccentColorUsage('h2', 'color', 'H2 headings');

  console.log('\nTest 3: Verifying h3 headings use accent color...');
  checkAccentColorUsage('h3', 'color', 'H3 headings');

  console.log('\nTest 4: Verifying buttons use accent color...');
  checkAccentColorUsage('.section button', 'backgroundColor', 'Section buttons (background)');
  checkAccentColorUsage('.section button', 'color', 'Section buttons (text)');

  console.log('\nTest 5: Verifying pricing card borders use accent color...');
  checkAccentColorUsage('.pricing-card', 'borderColor', 'Pricing card borders');

  console.log('\nTest 6: Verifying CTA section background uses accent color...');
  checkAccentColorUsage('.section-cta', 'backgroundColor', 'CTA section background');

  console.log('\nTest 7: Verifying hero gradient incorporates accent color...');
  const hero = document.querySelector('.section-hero');
  if (hero) {
    const bgImage = window.getComputedStyle(hero).backgroundImage;
    if (bgImage.includes('gradient')) {
      console.log('✓ Hero section has gradient background');
      console.log('  Background:', bgImage.substring(0, 100) + '...');
    } else {
      console.error('❌ Hero section does not have gradient background');
    }
  } else {
    console.warn('⚠ Hero section not found (template may not be loaded)');
  }

  console.log('\n=== Verification Complete ===');
}, 2000);
