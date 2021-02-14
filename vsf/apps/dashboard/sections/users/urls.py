from django.conf.urls import include
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path(
        '',
        views.UsersList.as_view(),
        name="users_list"
    ),     

    path(
        'register/',
        views.UserCreateView.as_view(),
        name="users_create"
    ),   

]