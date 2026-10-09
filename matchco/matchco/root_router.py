"""Roteador da raiz `/`.

Regra do SaaS:
- Anônimo → landing pública MatchCo renderizada na própria raiz.
- Autenticado → app autenticado (cursos, trilhas, feed, Wiki e notificações).

O site institucional matchco.com fica em outro deploy (Vercel/Webflow).
O app fica em app.matchco.com e nunca serve marketing na raiz.
"""
from django.shortcuts import redirect, render

def root(request):
    if request.user.is_authenticated:
        return redirect('app:dashboard')
    return render(request, 'recruitment/matchco_site/platform.html')
