from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from . import views
from library.views import ContentItemDetailView

urlpatterns = [
     path('content/<int:pk>/', login_required(ContentItemDetailView.as_view(), login_url='/login/'),
          name='student_library_content_detail'),
     path('register/',
          login_required(views.StudentRegistrationView.as_view(), login_url='/login/'),
          name='student_registration'),
     path('enroll-course/',
          login_required(views.StudentEnrollCourseView.as_view(), login_url='/login/'),
          name='student_enroll_course'),
     path('courses/',
          login_required(views.StudentCourseListView.as_view(), login_url='/login/'),
          name='student_course_list'),
     path('course/<pk>/',
          login_required(views.StudentCourseDetailView.as_view(), login_url='/login/'),
          name='student_course_detail'),
     path('course/<pk>/<module_id>/',
          login_required(views.StudentCourseDetailView.as_view(), login_url='/login/'),
          name='student_course_detail_module'),
     path('course/<pk>/module/<module_id>/content/<content_id>/<model_name>/',
          login_required(views.StudentContentDetailView.as_view(), login_url='/login/'),
          name='student_course_detail_module_content'),
     path('course/<pk>/module/<module_id>/content/<content_id>/<model_name>/next/',
          login_required(views.get_next_content, login_url='/login/'),
          name='student_course_next_module_content'),
     path('course/<pk>/module/<module_id>/content/<content_id>/<model_name>/back/',
          login_required(views.get_back_content, login_url='/login/'),
          name='student_course_back_module_content'),     
     path('course/<pk>/module/<module_id>/content/<content_id>/quiz/save/',
          login_required(views.save_quiz_view, login_url='/login/'),
          name='save_quiz_view'),
     # path('course/<pk>/completed/',
     #      login_required(views.StudentCourseCompletedView.as_view(), login_url='/login/'),
     #      name='student_course_completed')
]
