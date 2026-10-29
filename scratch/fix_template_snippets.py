import glob

files = [
    'templates/student.html',
    'templates/layouts/student_layout.html',
    'templates/layouts/lecturer_layout.html',
    'templates/layouts/faculty_layout.html'
]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace broken replace('\n', ' ') with clean Jinja filter
    old_snippet = """| striptags | replace('
', ' ') |"""
    new_snippet = """| striptags | replace('\\n', ' ') |"""

    if old_snippet in content:
        content = content.replace(old_snippet, new_snippet)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned snippet in {file_path}")
    else:
        print(f"Snippet not found in {file_path}")

