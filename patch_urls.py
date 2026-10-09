import re
path = '/Users/franco/Dev/matchco/matchco/recruitment/urls_public.py'
with open(path, 'r') as f:
    content = f.read()

new_routes = """
    # ---- Novas rotas do site institucional MatchCo ----
    path('matchco/como-funciona/', views.TemplateView.as_view(template_name='recruitment/matchco_site/como-funciona.html'), name='matchco_como_funciona'),
    path('matchco/para-shoppings/', views.TemplateView.as_view(template_name='recruitment/matchco_site/para-shoppings.html'), name='matchco_para_shoppings'),
    path('matchco/para-lojas/', views.TemplateView.as_view(template_name='recruitment/matchco_site/para-lojas.html'), name='matchco_para_lojas'),
    path('matchco/para-voce/', views.TemplateView.as_view(template_name='recruitment/matchco_site/para-voce.html'), name='matchco_para_voce'),
    path('matchco/perguntas/', views.TemplateView.as_view(template_name='recruitment/matchco_site/perguntas.html'), name='matchco_perguntas'),
"""

if 'matchco_como_funciona' not in content:
    content = content.replace("path('matchco/', views.MatchcoLandingView.as_view(), name='matchco_landing'),", 
                              "path('matchco/', views.MatchcoLandingView.as_view(), name='matchco_landing'),\n" + new_routes)

with open(path, 'w') as f:
    f.write(content)
