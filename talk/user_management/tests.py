from django.test import TestCase
from user_management.models import User
from django.test import Client
from .forms import *

from model_mommy import mommy


class UserTestCase(TestCase):
    def setUp(self):
        self.user = mommy.make('user_management.User', mobile='997998665', indication_code='1234')

    def tearDown(self):
        User.objects.all().delete()

    def test_mobile(self):
        user = User.objects.all()
        self.assertEqual(len(user), 1)



class Setup_Class(TestCase):

    def setUp(self):
        self.user = User.objects.create(password='user', last_login=None, is_superuser=False,
                                        username='este@teste.com', email='teste@teste.com', first_name='tt',
                                        last_name='ttt', mobile='1111111111', is_staff=True, is_active=True,
                                        data_join=None, indication_code='97859')


class User_Form_Test(TestCase):

    # Valid Form Data
    def test_UserForm_valid(self):
        form = CustomUserCreationForm(
            data={'password': "user", 'last_login': None, 'is_superuser': False, 'username': "teste@teste.com",
                  'email': "teste@teste.com", 'first_name': "tt", 'last_name': "ttt",
                  'mobile': 1111111111, 'is_staff': True, 'is_active': True,
                  'data_join': None, 'indication_code': 97859})
        self.assertTrue(form.is_valid())

    def test_UserForm_invalid(self):
        form = CustomUserCreationForm(
            data={'password': "", 'last_login': "", 'is_superuser': "", 'username': "",
                  'email': "", 'first_name': "", 'last_name': "",
                  'mobile': "", 'is_staff': "", 'is_active': "",
                  'data_join': "", 'indication_code': ""})
        self.assertFalse(form.is_valid())

# "password", "last_login", "is_superuser", "username", "first_name", "last_name", "email", "is_staff", "is_active", "date_joined", "mobile", "indication_code"
