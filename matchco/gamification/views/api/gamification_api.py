import json

from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from gamification.models import GamificationSettings


class GamificationSettingsSerializer(ModelSerializer):
    class Meta:
        model = GamificationSettings
        fields = '__all__'


class GetGamificationSettingsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        settings = get_object_or_404(GamificationSettings, pk=1)

        response = {
            'feed_post_view': settings.ap_feed_post_view,
            'course_enrollment': settings.ap_course_enrollment,
            'course_completation': settings.ap_course_completation,
            'passed_tests': settings.ap_passed_tests,
        }

        return Response(response)
