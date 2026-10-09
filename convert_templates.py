import os
import re

src_dir = '/Users/franco/Downloads/matchco-site-v0.3'
dst_dir = '/Users/franco/Dev/matchco/matchco/recruitment/templates/recruitment/matchco_site'

os.makedirs(dst_dir, exist_ok=True)

html_files = [f for f in os.listdir(src_dir) if f.endswith('.html')]

for html_file in html_files:
    with open(os.path.join(src_dir, html_file), 'r', encoding='utf-8') as f:
        content = f.read()

    # Add load static at the top if not present
    if '{% load static' not in content:
        content = '{% load static %}\n' + content

    # Replace assets/ with {% static 'matchco_site/
    # E.g., src="assets/img/img02-800.jpg" -> src="{% static 'matchco_site/img/img02-800.jpg' %}"
    content = re.sub(r'(src|href)="assets/([^"]+)"', r'\1="{% static \'matchco_site/\2\' %}"', content)
    content = re.sub(r'srcset="assets/([^"]+)"', r'srcset="{% static \'matchco_site/\1\' %}"', content)
    
    # Also need to replace inside imagesrcset
    def replace_srcset(match):
        urls = match.group(1).split(', ')
        replaced = []
        for u in urls:
            parts = u.split(' ')
            if parts[0].startswith('assets/'):
                parts[0] = f"{{% static 'matchco_site/{parts[0][7:]}' %}}"
            replaced.append(' '.join(parts))
        return 'imagesrcset="' + ', '.join(replaced) + '"'
        
    content = re.sub(r'imagesrcset="([^"]+)"', replace_srcset, content)
    
    def replace_srcset2(match):
        urls = match.group(1).split(', ')
        replaced = []
        for u in urls:
            parts = u.split(' ')
            if parts[0].startswith('assets/'):
                parts[0] = f"{{% static 'matchco_site/{parts[0][7:]}' %}}"
            replaced.append(' '.join(parts))
        return 'srcset="' + ', '.join(replaced) + '"'

    content = re.sub(r'srcset="([^"]+)"', replace_srcset2, content)

    # Link conversao: conversar.html -> # (for now, or maybe the matchco_role_chooser?)
    # For now, let's just keep the HTML links or route them via django URLs if requested later.
    
    with open(os.path.join(dst_dir, html_file), 'w', encoding='utf-8') as f:
        f.write(content)

print("Templates converted!")
