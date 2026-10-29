import re

path = 'static/assets/js/app.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Target broken regex with literal newline
old_block_part = text[text.find('// Tìm tên Đề tài & Tệp'):text.find('if (topicMatch) {')]
print("FOUND BLOCK:\n", repr(old_block_part))

new_block = """// Tìm tên Đề tài & Tệp
    const topicRegex = /Đề tài:\\s*(?:<strong>)?(.*?)(?:<\\/strong>)?(?:\\s*\\((.*?)\\))?(?:<\\/p>|<br>|[\\r\\n]|$)/i;
    const topicMatch = mainHtml.match(topicRegex) 
                    || mainHtml.match(/đề tài NCKH(?:\\s*<strong>)?:\\s*(.*?)(?:<\\/strong>)?(?:<\\/p>|<br>|[\\r\\n]|$)/i)
                    || mainHtml.match(/đề tài\\s*(?:<strong>)?["'“]?([^"'”<]+)["'”]?/i);
    """

if old_block_part:
    text = text.replace(old_block_part, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESSFULLY REPLACED IN app.js")
else:
    print("Block not found!")

