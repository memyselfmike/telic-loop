# Manual Test Plan for Task 2.4: Accent Color Picker Enhancement

## Pre-requisites
- Server running on http://localhost:3000
- Browser with developer tools

## Test Steps

### Test 1: Color Picker Has Label
1. Open http://localhost:3000
2. Look at the preview controls area
3. **Expected**: See a label "Accent Color:" next to the color picker input
4. **Status**: ✅ Label added in index.html

### Test 2: Changing Accent Color Updates CSS Variable Immediately
1. Load any template (e.g., SaaS Product)
2. Click the color picker
3. Select a distinctive color (e.g., bright orange #ff5733)
4. Open browser DevTools → Inspect the root element (html or :root)
5. **Expected**: --accent-color CSS variable shows the new color immediately
6. **Status**: ✅ Implemented in renderPreview() at line 98 of app.js

### Test 3: All H2 Headings Use Accent Color
1. With a template loaded and custom accent color set
2. Inspect each h2 element (Features, Testimonials, Pricing, CTA)
3. **Expected**: All h2 elements have color matching the accent color
4. **CSS Rules**:
   - .section-features h2 (line 44)
   - .section-testimonials h2 (line 78)
   - .section-pricing h2 (line 115)
   - .section-cta h2 (line 176)
5. **Status**: ✅ All use var(--accent-color)

### Test 4: All H3 Headings Use Accent Color
1. Check h3 elements in Features section and Pricing section
2. **Expected**: All h3 elements have color matching the accent color
3. **CSS Rules**:
   - .feature-card h3 (line 67)
   - .pricing-card h3 (line 136)
4. **Status**: ✅ All use var(--accent-color)

### Test 5: All Buttons Use Accent Color
1. Inspect buttons across all sections
2. **Expected**: Each button uses accent color for either background or text:
   - Hero button: white background, accent color text
   - Pricing buttons: accent color background, white text
   - CTA button: white background, accent color text
3. **CSS Rules**:
   - .section-hero button (line 31: color)
   - .pricing-card button (line 158: background)
   - .section-cta button (line 189: color)
4. **Status**: ✅ All buttons use var(--accent-color)

### Test 6: Pricing Card Borders Use Accent Color
1. Scroll to pricing section
2. Inspect the border of pricing cards
3. Change accent color and verify borders update
4. **Expected**: All pricing card borders match the accent color
5. **CSS Rule**: .pricing-card (line 127: border-color)
6. **Status**: ✅ Changed from #e5e7eb to var(--accent-color)

### Test 7: CTA Section Background Uses Accent Color
1. Scroll to CTA section (bottom of page)
2. Inspect the background
3. Change accent color and verify background updates
4. **Expected**: CTA section background matches the accent color
5. **CSS Rule**: .section-cta (line 170: background)
6. **Status**: ✅ Uses var(--accent-color)

### Test 8: Hero Gradient Incorporates Accent Color
1. Inspect the hero section background
2. Change accent color and verify gradient updates
3. **Expected**: Hero gradient starts with the accent color and transitions to #1e40af
4. **CSS Rule**: .section-hero (line 12: linear-gradient with var(--accent-color))
5. **Status**: ✅ Uses var(--accent-color) in gradient

### Test 9: Verify Across All 3 Templates
Repeat tests 3-8 for each template:
- SaaS Product
- Event/Webinar
- Portfolio Showcase

### Test 10: Export Verification
1. Load a template
2. Change accent color to a distinctive color
3. Click "Export HTML"
4. Open the downloaded landing-page.html in a browser
5. **Expected**: All elements should reflect the accent color exactly as shown in the preview
6. **Status**: ✅ getCombinedCSS() includes updated pricing card border rule

## Acceptance Criteria Verification

✅ 1. Changing accent color updates --accent-color CSS variable immediately
✅ 2. All h2/h3 headings use accent color
✅ 3. All buttons use accent color (background or text)
✅ 4. Pricing card borders use accent color
✅ 5. CTA section background uses accent color
✅ 6. Hero gradient incorporates accent color
✅ BONUS: Color picker has label for clarity

## Files Modified
- public/index.html: Added label for color picker
- public/css/templates.css: Updated pricing card border to use var(--accent-color)
- public/js/app.js: Updated getSectionCSS() to match templates.css changes
