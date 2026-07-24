import pytz

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib import messages
from django import forms
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import get_language, gettext as _
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseRedirect

from .forms import CustomUserEditForm, CustomUserCreationForm, UserAvatarForm
from .models import UserProfile
from configuration.services import management_access

from gamification.models import GamificationReport, Badges
from gamification.views.gamification import HistoricPointsListView


User = get_user_model()


# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = 'user_management.add_user'
change_user_perm = 'user_management.change_user'
delete_user_perm = 'user_management.delete_user'


class SearchForm(forms.Form):
    q = forms.CharField(required=False, label=_('Search users'))


def any_permission_required(*permissions):
    def decorator(view_func):
        def allowed(user):
            return user.is_authenticated and (user.is_superuser or any(user.has_perm(p) for p in permissions))
        return user_passes_test(allowed, login_url='/login/')(view_func)
    return decorator


@any_permission_required(add_user_perm, change_user_perm, delete_user_perm)
@vary_on_headers('X-Requested-With')
def index(request, *args):
    q = None
    is_searching = False

    group = None
    group_filter = Q()
    if args:
        group = get_object_or_404(Group, id=args[0])
        group_filter = Q(groups=group) if args else Q()

    model_fields = [f.name for f in User._meta.get_fields()]

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search users"))
        if form.is_valid():
            q = form.cleaned_data['q']
            is_searching = True
            conditions = Q()

            for term in q.split():
                if 'username' in model_fields:
                    conditions |= Q(username__icontains=term)

                if 'first_name' in model_fields:
                    conditions |= Q(first_name__icontains=term)

                if 'last_name' in model_fields:
                    conditions |= Q(last_name__icontains=term)

                if 'email' in model_fields:
                    conditions |= Q(email__icontains=term)

            users = User.objects.filter(group_filter & conditions)
    else:
        form = SearchForm(placeholder=_("Search users"))

    if not is_searching:
        if request.user.is_companyunit_manager_group():
            membership = request.user.primary_membership
            users = User.objects.filter(memberships__business_unit=membership.business_unit).distinct() if membership and membership.business_unit_id else User.objects.none()
        else:
            users = User.objects.filter(group_filter)

    if 'last_name' in model_fields and 'first_name' in model_fields:
        users = users.order_by('last_name', 'first_name')

    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering == 'username':
            users = users.order_by(User.USERNAME_FIELD)
    else:
        ordering = 'name'

    paginator = Paginator(users, per_page=20)
    users = paginator.get_page(request.GET.get('p'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return TemplateResponse(request, "user_management/users/results.html", {
            'users': users,
            'is_searching': is_searching,
            'query_string': q,
            'ordering': ordering,
        })
    else:
        return TemplateResponse(request, "user_management/users/index.html", {
            'group': group,
            'search_form': form,
            'users': users,
            'is_searching': is_searching,
            'ordering': ordering,
            'query_string': q,
        })


@permission_required(change_user_perm)
def edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    can_delete = request.user.is_superuser and user != request.user
    editing_self = request.user == user

    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()

            if user == request.user and 'password1' in form.changed_data:
                # User is changing their own password; need to update their session hash
                update_session_auth_hash(request, user)

            messages.success(request, _("User '{0}' updated.").format(user))
            return redirect('usermanagement_users:index')
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = CustomUserEditForm(instance=user)
    return TemplateResponse(request, 'user_management/users/edit.html', {
        'user': user,
        'form': form,
        'can_delete': can_delete,
    })


@permission_required(add_user_perm, raise_exception=True)
def add(request):
    form = CustomUserCreationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('User created.'))
        return redirect('usermanagement_users:index')
    return render(request, 'user_management/users/form.html', {'form': form, 'title': _('Add user')})


@permission_required(delete_user_perm, raise_exception=True)
def delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, _('You cannot delete your own account.'))
    elif request.method == 'POST':
        user.delete()
        messages.success(request, _('User deleted.'))
    return redirect('usermanagement_users:index')


class UserProfileDetailView(DetailView):
    model = User
    template_name = "user_management/profile/dashboard.html"
    context_object_name = 'user_profile'

    def get_course_infos(self, user):
        enrollment = GamificationReport.objects.filter(user=user.id, type_event='course_enrollment').count()
        completed = GamificationReport.objects.filter(user=user.id, type_event='course_completation').count()
        certificated = None
        
        return {
            'courses_enrollment': enrollment,
            'courses_completed': completed,
            'courses_certificated': certificated,
        }

    def get_quizz_infos(self, user):
        started = None
        finished = None
        score = None
        
        return {
            'quizz_started': started,
            'quizz_finished': finished,
            'quizz_score': score,
        }

    def get_actual_badge(self, points):
        badges = Badges.objects.all().order_by('qty_points')
        
        for badge in badges:
            if badge.qty_points <= points:
                return badge
        
        return None
    
    def get_context_data(self, **kwargs):
        res = super().get_context_data(**kwargs)
        
        user = self.object
        user_profile, profile_created = UserProfile.objects.get_or_create(user=user)
        memberships = list(user.memberships.filter(active=True).select_related(
            'organization', 'company', 'business_unit', 'operational_unit'
        ).prefetch_related('channels', 'functions'))

        courses = self.get_course_infos(user)
        quizz = self.get_quizz_infos(user)

        badge = self.get_actual_badge(user.current_points)
        languages = {
            'pt-br': _('Brazilian Portuguese'),
            'es': _('Spanish'),
            'en': _('English'),
        }
        password_form = kwargs.get('password_form') or PasswordChangeForm(user=self.request.user)
        avatar_form = kwargs.get('avatar_form') or UserAvatarForm(instance=user_profile)
        input_classes = 'block w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400'
        for field in password_form.fields.values():
            field.widget.attrs['class'] = input_classes
        avatar_form.fields['avatar'].widget.attrs['class'] = 'block w-full cursor-pointer rounded-lg border border-gray-300 bg-gray-50 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300'

        res.update({
            'profile_user': user,
            'courses_enrollment': courses.get('courses_enrollment'),
            'courses_completed': courses.get('courses_completed'),
            'courses_certificated': courses.get('courses_certificated'),
            'quizz_started': quizz.get('quizz_started'),
            'quizz_finished': quizz.get('quizz_finished'),
            'quizz_score': quizz.get('quizz_score'),
            'badge': badge,
            'user_profile': user_profile,
            'preferred_language': languages.get(get_language())
            , 'memberships': memberships,
            'membership_count': len(memberships),
            'organization_count': len({item.organization_id for item in memberships}),
            'can_edit_enterprise': management_access.can_manage_user(self.request.user, user),
            'can_edit_account': self.object.pk == self.request.user.pk,
            'password_form': password_form,
            'avatar_form': avatar_form,
            'language_code': get_language(),
            'timezones': pytz.common_timezones,
        })

        return res

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.pk != request.user.pk:
            return HttpResponseRedirect(reverse_lazy('user_management_profile:user_profile_detail', kwargs={'pk': request.user.pk}))
        action = request.POST.get('action')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if action == 'password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Senha atualizada com sucesso.')
                return redirect('user_management_profile:user_profile_detail', pk=request.user.pk)
            return self.render_to_response(self.get_context_data(password_form=form))
        if action == 'avatar':
            form = UserAvatarForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Foto do perfil atualizada com sucesso.')
                return redirect('user_management_profile:user_profile_detail', pk=request.user.pk)
            return self.render_to_response(self.get_context_data(avatar_form=form))
        if action == 'timezone':
            timezone = request.POST.get('timezone')
            if timezone in pytz.common_timezones:
                request.session['django_timezone'] = timezone
                profile.current_time_zone = timezone
                profile.save(update_fields=['current_time_zone'])
                messages.success(request, 'Fuso horário atualizado com sucesso.')
            return redirect('user_management_profile:user_profile_detail', pk=request.user.pk)
        return redirect('user_management_profile:user_profile_detail', pk=request.user.pk)

    def get(self, request, *args, **kwargs):
        res = super().get(request, *args, **kwargs)
        
        user_profile = UserProfile.objects.filter(user=request.user.id).first()
        if not user_profile:
            user_profile = UserProfile(user=request.user)
            user_profile.save()

        return res


class UserProfileGamificationPoints(HistoricPointsListView):
    template_name = 'user_management/gamification/user_points.html'


def redirect_profile_settings(request):
    return redirect('user_management_profile:user_profile_detail', pk=request.user.pk)
