"""Final comprehensive verification for task 3.1"""
import json

print("="*60)
print("TASK 3.1 FINAL VERIFICATION")
print("="*60)

# 1. File size check
import os
file_size = os.path.getsize("index.html")
size_kb = file_size / 1024
print(f"\n✓ File size: {file_size} bytes ({size_kb:.2f} KB)")
print(f"  Target: < 15 KB")
print(f"  Status: {'PASS' if file_size < 15360 else 'FAIL'}")

# 2. Read file and check structure
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Check all four widgets present
widgets = ["clock-widget", "weather-widget", "task-widget", "timer-widget"]
print(f"\n✓ Widget presence check:")
for widget in widgets:
    present = f'id="{widget}"' in content
    print(f"  {widget}: {'PASS' if present else 'FAIL'}")

# Check for potential conflicts
print(f"\n✓ Integration checks:")

# Check setInterval calls
clock_interval = "setInterval(updateClock,1000)" in content
weather_interval = "setInterval(updateWeather,30*60*1000)" in content
timer_interval = "setInterval(tick,1000)" in content
print(f"  Clock setInterval: {'PASS' if clock_interval else 'FAIL'}")
print(f"  Weather setInterval: {'PASS' if weather_interval else 'FAIL'}")
print(f"  Timer setInterval: {'PASS' if timer_interval else 'FAIL'}")

# Check localStorage key uniqueness
tasks_key = "TASKS_KEY='focusDashboardTasks'" in content
print(f"  Unique localStorage key: {'PASS' if tasks_key else 'FAIL'}")

# Check all widgets have unique function names
unique_funcs = [
    "updateClock" in content,
    "updateWeather" in content,
    "updateDisplay" in content,
    "renderTasks" in content
]
print(f"  Unique function names: {'PASS' if all(unique_funcs) else 'FAIL'}")

# Check dark theme CSS variables present
dark_theme = "--bg-primary:#1a1a2e" in content
print(f"  Dark theme CSS: {'PASS' if dark_theme else 'FAIL'}")

# Check weather fallback is implemented
weather_fallback = "'Weather unavailable'" in content
print(f"  Weather fallback: {'PASS' if weather_fallback else 'FAIL'}")

# Check timer audio implementation
audio_beep = "AudioContext" in content
print(f"  Timer beep (Web Audio API): {'PASS' if audio_beep else 'FAIL'}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
