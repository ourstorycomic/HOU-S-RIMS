import re

with open('static/assets/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in app.js: {len(lines)}")

# Check for regex literal spanning multiple lines
for i in range(1750, 1820):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end='')

