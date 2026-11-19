"""
Views para a Web App MatchCo em /app/*

Todas as views requerem autenticação e organização selecionada.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView, ListView
from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from configuration.organization_context import selected_organization
from home.views import home as main_app_home
from user_management.forms import UserAvatarForm
from user_management.models import UserProfile


class AppProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email')
        labels = {'first_name': 'Primeiro nome', 'last_name': 'Sobrenome', 'email': 'E-mail'}
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-heading dark:border-gray-600 dark:bg-gray-700 dark:text-white'


class AppBaseView(LoginRequiredMixin, TemplateView):
    """
    View base para toda a app.
    Garante que:
    - Usuário está autenticado
    - Organização foi selecionada
    - Contexto da app está disponível
    """
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        # Verificar se tem organização selecionada
        org = selected_organization(request)
        if not org:
            return redirect('select-organization')

        # The app always runs inside the organization selected in the
        # session. This is also the boundary used by audience evaluation.
        request.user._active_organization_id = org.pk
        if not hasattr(request.user, '_active_company_id'):
            request.user._active_company_id = getattr(request, 'active_company_id', None)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = selected_organization(self.request)
        context['user'] = self.request.user
        return context


# ============================================================================
# DASHBOARD
# ============================================================================

class AppDashboardView(AppBaseView):
    """Dashboard principal da app."""

    def get(self, request, *args, **kwargs):
        # Reuse the mature, audience-aware application home. The URL is now
        # /app/, while the institutional root remains public.
        return main_app_home(request)


# ============================================================================
# PERFIL E CONFIGURAÇÕES
# ============================================================================

class AppProfileView(AppBaseView):
    """Visualizar perfil do usuário."""
    template_name = 'app/profile/view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Meu Perfil'
        context['user_profile'], _ = UserProfile.objects.get_or_create(user=self.request.user)
        return context


class AppProfileEditView(AppBaseView):
    """Editar perfil do usuário."""
    template_name = 'app/profile/edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Editar Perfil'
        profile = UserProfile.objects.get_or_create(user=self.request.user)[0]
        context['profile_form'] = kwargs.get('profile_form') or AppProfileForm(instance=self.request.user)
        context['avatar_form'] = kwargs.get('avatar_form') or UserAvatarForm(instance=profile)
        context['user_profile'] = profile
        return context

    def post(self, request, *args, **kwargs):
        profile = UserProfile.objects.get_or_create(user=request.user)[0]
        profile_form = AppProfileForm(request.POST, instance=request.user)
        avatar_form = UserAvatarForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid() and avatar_form.is_valid():
            profile_form.save()
            avatar_form.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('app:profile')
        return self.render_to_response(self.get_context_data(profile_form=profile_form, avatar_form=avatar_form))


class AppSettingsView(AppBaseView):
    """Configurações da conta."""
    template_name = 'app/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Configurações'
        return context


# ============================================================================
# CURSOS E APRENDIZADO
# ============================================================================

class AppCoursesView(AppBaseView):
    """Lista de cursos do usuário."""
    template_name = 'app/courses/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Meus Cursos'
        # TODO: Buscar cursos do usuário
        return context


class AppCourseDetailView(AppBaseView):
    """Detalhes de um curso."""
    template_name = 'app/courses/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        context['page_title'] = 'Curso'
        context['course_id'] = course_id
        # TODO: Buscar dados do curso
        return context


class AppCoursePlayerView(AppBaseView):
    """Player de curso."""
    template_name = 'app/courses/player.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        context['page_title'] = 'Assistindo Curso'
        context['course_id'] = course_id
        # TODO: Carregar player do curso
        return context


class AppCourseProgressView(AppBaseView):
    """Progresso do curso."""
    template_name = 'app/courses/progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        context['page_title'] = 'Progresso do Curso'
        context['course_id'] = course_id
        return context


# ============================================================================
# FEED E OPORTUNIDADES
# ============================================================================

class AppFeedView(AppBaseView):
    """Feed principal da app."""
    template_name = 'app/feed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Feed'
        from publishing.models import Publication
        org = selected_organization(self.request)
        if org:
            context['publications'] = Publication.objects.filter(
                status='published', kind='feed'
            ).order_by('-published_at')[:10]
        return context


class AppTrailsView(AppBaseView):
    """Minhas trilhas de aprendizado."""
    template_name = 'app/trails.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Minhas Trilhas'
        from students.models import TrailAssignment
        context['assignments'] = TrailAssignment.objects.filter(
            user=self.request.user
        ).select_related('trail').order_by('-created_at')
        return context


class AppWikiView(AppBaseView):
    """Base de conhecimento e wikis."""
    template_name = 'app/wiki.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Wiki'
        from publishing.models import Publication
        context['publications'] = Publication.objects.filter(
            status='published', kind='wiki'
        ).order_by('-published_at')[:12]
        return context


class AppOpportunitiesView(AppBaseView):
    """Lista de oportunidades."""
    template_name = 'app/opportunities.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Oportunidades'
        # TODO: Carregar oportunidades
        return context


# ============================================================================
# MATCHES E CONVERSAS
# ============================================================================

class AppMatchesView(AppBaseView):
    """Lista de matches."""
    template_name = 'app/matches/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Matches'
        # TODO: Carregar matches
        return context


class AppMatchDetailView(AppBaseView):
    """Detalhes de um match."""
    template_name = 'app/matches/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match_id = kwargs.get('match_id')
        context['page_title'] = 'Match'
        context['match_id'] = match_id
        # TODO: Carregar dados do match e conversas
        return context


# ============================================================================
# ============================================================================
# HELP E DOCUMENTAÇÃO
# ============================================================================

class AppHelpView(AppBaseView):
    """Centro de ajuda da app."""
    template_name = 'app/help/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajuda'
        # TODO: Carregar tópicos de ajuda
        return context


class AppHelpTopicView(AppBaseView):
    """Tópico específico de ajuda."""
    template_name = 'app/help/topic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = kwargs.get('topic')
        context['page_title'] = f'Ajuda: {topic}'
        context['topic'] = topic
        # TODO: Carregar conteúdo do tópico
        return context


# ============================================================================
# NOTIFICAÇÕES
# ============================================================================

class AppNotificationsView(AppBaseView):
    """Centro de notificações."""
    template_name = 'app/notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Notificações'
        # TODO: Carregar notificações
        return context


class AppNotificationReadView(AppBaseView):
    """Marcar notificação como lida (AJAX)."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        notification_id = kwargs.get('notification_id')
        # TODO: Marcar como lida
        return JsonResponse({'status': 'ok', 'notification_id': notification_id})
