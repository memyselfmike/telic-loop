
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Collect console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    consoleMessages.push({ type, text });
    console.log(`[${type.toUpperCase()}] ${text}`);
  });
  
  // Collect errors
  const errors = [];
  page.on('pageerror', error => {
    errors.push(error.message);
    console.log(`[ERROR] ${error.message}`);
  });
  
  // Navigate to the page
  await page.goto('http://localhost:8000/index.html');
  
  // Wait for page to load
  await page.waitForTimeout(2000);
  
  // Check all four widgets are present
  const clockWidget = await page.locator('#clock-widget').count();
  const weatherWidget = await page.locator('#weather-widget').count();
  const taskWidget = await page.locator('#task-widget').count();
  const timerWidget = await page.locator('#timer-widget').count();
  
  console.log(`
Widget Check:`);
  console.log(`Clock Widget: ${clockWidget === 1 ? 'PASS' : 'FAIL'}`);
  console.log(`Weather Widget: ${weatherWidget === 1 ? 'PASS' : 'FAIL'}`);
  console.log(`Task Widget: ${taskWidget === 1 ? 'PASS' : 'FAIL'}`);
  console.log(`Timer Widget: ${timerWidget === 1 ? 'PASS' : 'FAIL'}`);
  
  // Check clock is updating
  const clockTime = await page.locator('#clock-time').textContent();
  console.log(`
Clock displays: ${clockTime}`);
  
  // Check weather shows fallback (no API key)
  const weatherInfo = await page.locator('#weather-info').textContent();
  console.log(`Weather displays: ${weatherInfo}`);
  
  // Check task count
  const taskCount = await page.locator('#task-count').textContent();
  console.log(`Task count displays: ${taskCount}`);
  
  // Check timer display
  const timerDisplay = await page.locator('#timer-display').textContent();
  console.log(`Timer displays: ${timerDisplay}`);
  
  console.log(`
Total errors: ${errors.length}`);
  
  await browser.close();
  
  process.exit(errors.length > 0 ? 1 : 0);
})();
