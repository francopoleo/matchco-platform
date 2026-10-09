from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('mine/',
         login_required(views.ManageCourseListView.as_view(), login_url='/login/'),
         name='manage_course_list'),

    path('create/',
         login_required(views.CourseCreateView.as_view(), login_url='/login/'),
         name='course_create'),

    path('<pk>/edit/',
         login_required(views.CourseUpdateView.as_view(), login_url='/login/'),
         name='course_edit'),

    path('<pk>/delete/',
         login_required(views.CourseDeleteView.as_view(), login_url='/login/'),
         name='course_delete'),

    path('<pk>/module/',
         login_required(views.CourseModuleUpdateView.as_view(), login_url='/login/'),
         name='course_module_update'),

    path('module/<int:module_id>/content/<model_name>/create/',
         login_required(views.ContentCreateUpdateView.as_view(), login_url='/login/'),
         name='module_content_create'),

    path('module/<int:module_id>/content/<model_name>/<id>/',
         login_required(views.ContentCreateUpdateView.as_view(), login_url='/login/'),
         name='module_content_update'),

    path('content/<int:id>/delete/',
         login_required(views.ContentDeleteView.as_view(), login_url='/login/'),
         name='module_content_delete'),

    path('module/<int:module_id>/',
         login_required(views.ModuleContentListView.as_view(), login_url='/login/'),
         name='module_content_list'),

    path('module/order/',
         login_required(views.ModuleOrderView.as_view(), login_url='/login/'),
         name='module_order'),

    path('content/order/',
         login_required(views.ContentOrderView.as_view(), login_url='/login/'),
         name='content_order'),

    path('subject/<slug:subject>/',
         login_required(views.CourseListView.as_view(), login_url='/login/'),
         name='course_list_subject'),

    path('test/subject/<slug:subject>/',
         login_required(views.TestListView.as_view(), login_url='/login/'),
         name='test_list_subject'),

    path('<slug:slug>/',
         login_required(views.CourseDetailView.as_view(), login_url='/login/'),
         name='course_detail'),

    path('redirect/question/<int:item_id>/',
         login_required(views.QuestionCreateRedirectView.as_view(), login_url='/login/'),
         name='question_redirect_view'),
]
