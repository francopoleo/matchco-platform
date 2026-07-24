from django.contrib.auth import get_user_model
from django.test import TestCase
from .forms import UserSignupCreationForm

# Create your tests here.


UserModel = get_user_model()


class Setup_Class(TestCase):

    def setUp(self):
        self.user = UserModel.objects.create(indication_code=111, username='test@teste', first_name='teste',
                                             mobile='11111111', last_name='test', password1='user', password2='user')


class User_Form_Test(TestCase):

    # Valid Form Data
    def test_UserForm_valid(self):
        form = UserSignupCreationForm(
            data={'indication_code': 111, 'username': "test@teste", 'first_name': "teste",
                  'last_name': "test", 'mobile': 11111111, 'password1': "user", 'password2': "user"})
        self.assertFalse(form.is_valid())

  

