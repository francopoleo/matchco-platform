from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

from user_management.models import DemoVisit


def demo_access(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        company = request.POST.get('company', '').strip()
        if name and email and '@' in email:
            user = get_user_model().objects.get(username='demo', is_demo=True)
            if not request.session.session_key:
                request.session.create()
            visit = DemoVisit.objects.create(
                demo_user=user,
                session_key=request.session.session_key,
                visitor_name=name,
                visitor_email=email,
                visitor_company=company,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            request.session['demo_interest_id'] = visit.pk
            return render(request, 'registration/demo_access.html', {'submitted': True, 'name': name})
        return render(request, 'registration/demo_access.html', {'error': 'Informe seu nome e um e-mail válido.', 'name': name, 'email': email, 'company': company})
    return render(request, 'registration/demo_access.html')
