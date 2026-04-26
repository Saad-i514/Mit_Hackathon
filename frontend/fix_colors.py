import sys

file_path = 'app/(dashboard)/plans/page.tsx'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Colors
    content = content.replace('bg-white', 'bg-card text-card-foreground')
    content = content.replace('text-gray-900', 'text-foreground')
    content = content.replace('border-gray-100', 'border-border')
    content = content.replace('bg-gray-900', 'bg-secondary')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated plans/page.tsx')
except Exception as e:
    print(e)
