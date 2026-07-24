from django.urls import path

from user_management import views


app_name = 'usermanagement_users'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add, name='add'),
    path('<str:user_id>/', views.edit, name='edit'),
    path('<str:user_id>/delete/', views.delete, name='delete')
]
