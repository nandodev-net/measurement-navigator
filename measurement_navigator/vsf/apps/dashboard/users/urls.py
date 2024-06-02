from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.UsersList.as_view(), name="users_list"),
    path("register/", views.UserCreateView.as_view(), name="users_create"),
    path("create/", views.UserCreateModalView.as_view(), name="users_register"),
    path("<int:pk>", views.UserUpdateView.as_view(), name="user_edit"),
    path(
        "passreveal/<int:pk>",
        views.CustomUserPasswdRevealView.as_view(),
        name="user_reveal_pass",
    ),
    path("activation/<int:pk>", views.CurtomUserActivationView, name="user_activation"),
    path(
        "createpass/<int:pk>",
        views.CustomUserCreatePass.as_view(),
        name="user_pass_create",
    ),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
]
