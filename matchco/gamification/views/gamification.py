from django.views.generic import DetailView, UpdateView, ListView
from django.urls import reverse
from django.apps import apps

from user_management.models import User

from gamification.models import GamificationSettings, GamificationReport
from gamification.forms import GamificationSettingsModelForm
from gamification.permissions import permission_policy


class GamificationSettingsDetailView(DetailView):
    model = GamificationSettings
    template_name = 'gamification/settings/detail.html'
    context_object_name = 'settings'

    def get_context_data(self, **kwargs):
        res = super().get_context_data(**kwargs)

        res.update({
            'user_can_edit': permission_policy.user_has_permission(self.request.user, 'change')
        })

        return res


class GamificationSettingsUpdateView(UpdateView):
    model = GamificationSettings
    template_name = 'gamification/settings/edit.html'
    form_class = GamificationSettingsModelForm
    context_object_name = 'settings'

    def get_success_url(self):
        settings_id = self.get_object()
        return reverse('cepgamification:settings-detail', kwargs={'pk': settings_id.id})


class HistoricPointsListView(ListView):
    model = GamificationReport
    template_name = 'gamification/list_user_points.html'
    context_object_name = 'historic_points'

    def get_queryset(self):
        return self.model.objects.filter(user=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['user'] = User.objects.get(pk=self.kwargs['pk'])

        app = {
            'post_view': 'publishing',
            'course_enrollment': 'courses',
            'course_completation': 'courses',
            'passed_tests': 'courses'
        }
        model_aliases = {
            ('publishing', 'FeedPost'): 'Publication',
            ('publishing', 'WikiPost'): 'Publication',
        }
        points = []

        for obj in self.get_queryset():
            name = None
            if obj.id_source:
                app_label = app.get(obj.type_event)
                if not app_label or not obj.model_name:
                    points.append((obj, None))
                    continue
                model_name = model_aliases.get(
                    (app_label, obj.model_name), obj.model_name)
                try:
                    ObjectClass = apps.get_model(app_label, model_name=model_name)
                except LookupError:
                    points.append((obj, None))
                    continue
                Object = ObjectClass.objects.filter(pk=obj.id_source).first()
                if Object is None:
                    points.append((obj, None))
                    continue
                # name = Object.__dict__.get(event[obj.type_event])
                name = getattr(Object, 'title', str(Object))

                # if obj.type_event == 'passed_tests':
                #     score = Object.__dict__.get('points_per_approval')
                #     name += f"{score}"
            points.append((obj, name))

        context['points'] = points

        return context
