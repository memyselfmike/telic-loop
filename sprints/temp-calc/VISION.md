# Vision: Temperature Converter CLI

## The Promise

A developer working on a project needs to quickly convert temperatures between Celsius, Fahrenheit, and Kelvin from the command line. Currently they have to open a browser and use a web calculator — slow and interrupts their flow.

## The Outcome

After this sprint, the developer can run a single command like `python temp_calc.py 100 C F` and instantly see the converted temperature. It handles all three scales (C, F, K), validates input, and gives clear error messages for bad input.

## Success Signal

Running `python temp_calc.py 100 C F` prints `212.0` (100°C = 212°F).
Running `python temp_calc.py 32 F C` prints `0.0` (32°F = 0°C).
Running `python temp_calc.py 0 K C` prints `-273.15` (0K = -273.15°C).
Running `python temp_calc.py` with no args prints usage help.
Running `python temp_calc.py abc C F` prints a clear error about invalid input.
