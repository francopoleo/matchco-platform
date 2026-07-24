from django.forms import ModelForm

from gamification.models import GamificationSettings


class GamificationSettingsModelForm(ModelForm):
    
    class Meta:
        model = GamificationSettings
        fields = [
            'ap_first_login',
            'dp_first_login',
            'ap_feed_post_view',
            'dp_feed_post_view',
            'ap_course_enrollment',
            'dp_course_enrollment',
            'ap_course_completation',
            'dp_course_completation',
            'ap_passed_tests',
            'dp_passed_tests',
        ]
