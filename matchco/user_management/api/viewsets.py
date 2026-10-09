# import json

from django.contrib.auth.models import Group

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from user_management.models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'patch']:
            return [AllowAny(), ]
        return super(UserViewSet, self).get_permissions()

    def create(self, request, *args, **kwargs):
        res = super(UserViewSet, self).create(request, *args, **kwargs)
        return res
