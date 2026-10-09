import os

dst_dir = '/Users/franco/Dev/matchco/matchco/recruitment/templates/recruitment/matchco_site'
html_files = [f for f in os.listdir(dst_dir) if f.endswith('.html')]

replacements = {
    'href="index.html"': 'href="{% url \'recruitment_public:matchco_landing\' %}"',
    'href="como-funciona.html"': 'href="{% url \'recruitment_public:matchco_como_funciona\' %}"',
    'href="para-shoppings.html"': 'href="{% url \'recruitment_public:matchco_para_shoppings\' %}"',
    'href="para-lojas.html"': 'href="{% url \'recruitment_public:matchco_para_lojas\' %}"',
    'href="para-voce.html"': 'href="{% url \'recruitment_public:matchco_para_voce\' %}"',
    'href="perguntas.html"': 'href="{% url \'recruitment_public:matchco_perguntas\' %}"',
    'href="conversar.html"': 'href="{% url \'recruitment_public:matchco_role_chooser\' %}"',
}

for html_file in html_files:
    with open(os.path.join(dst_dir, html_file), 'r', encoding='utf-8') as f:
        content = f.read()
        
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(os.path.join(dst_dir, html_file), 'w', encoding='utf-8') as f:
        f.write(content)

print("Links fixed!")
