import sys

file_path = 'app/(dashboard)/plans/[id]/page.tsx'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Layout colors
    content = content.replace('bg-white', 'bg-background/60 backdrop-blur-md')
    content = content.replace('bg-gray-50', 'bg-card/50')
    
    # Text colors
    content = content.replace('text-gray-900', 'text-foreground')
    content = content.replace('text-gray-800', 'text-foreground/90')
    content = content.replace('text-gray-700', 'text-foreground/80')
    content = content.replace('text-gray-600', 'text-muted-foreground')
    content = content.replace('text-gray-500', 'text-muted-foreground')
    content = content.replace('text-gray-400', 'text-muted-foreground/80')
    
    # Borders
    content = content.replace('border-gray-100', 'border-white/10')
    content = content.replace('border-gray-50', 'border-white/5')
    content = content.replace('border-gray-200', 'border-white/20')

    # Specific tweaks
    content = content.replace('hover:bg-gray-50', 'hover:bg-card')
    content = content.replace('hover:bg-gray-100', 'hover:bg-muted')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated plans/[id]/page.tsx')
except Exception as e:
    print(e)
