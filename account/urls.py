from django.urls import path, include
from . import views
<<<<<<< HEAD
from django.contrib.auth import views as auth_views

=======
>>>>>>> 967e6de772d5851103f357be2a9c8386b7957e87

urlpatterns = [
    # previous login view
    # path('login/', views.user_login, name='login'),
<<<<<<< HEAD
=======
    # from django.contrib.auth import views as auth_views

>>>>>>> 967e6de772d5851103f357be2a9c8386b7957e87

    # path('login/', auth_views.LoginView.as_view(), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # change password urls
    # path('password-change/',
    #      auth_views.PasswordChangeView.as_view(),
    #      name='password_change'),
    # path('password-change/done/',
    #      auth_views.PasswordChangeDoneView.as_view(),
    #      name='password_change_done'),

    # reset password urls
<<<<<<< HEAD
    path('password-reset/',
         auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
=======
    # path('password-reset/',
    #      auth_views.PasswordResetView.as_view(),
    #      name='password_reset'),
    # path('password-reset/done/',
    #      auth_views.PasswordResetDoneView.as_view(),
    #      name='password_reset_done'),
    # path('password-reset/<uidb64>/<token>/',
    #      auth_views.PasswordResetConfirmView.as_view(),
    #      name='password_reset_confirm'),
    # path('password-reset/complete/',
    #      auth_views.PasswordResetCompleteView.as_view(),
    #      name='password_reset_complete'),
>>>>>>> 967e6de772d5851103f357be2a9c8386b7957e87

    path('', include('django.contrib.auth.urls')),
    # path('', views.dashboard, name='dashboard'),
    path('', views.home, name='home'),  # Homepage route
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('user/<username>/followers/', views.user_followers,
         name='user_followers'),
    path('user/<username>/following/', views.user_following,
         name='user_following'),
    path('not-following-back/', views.not_following_back,
         name='not_following_back'),
    path('users/', views.user_list, name='user_list'),
    path('users/follow/', views.user_follow, name='user_follow'),
    path('users/<username>/', views.user_detail, name='user_detail'),
    path('upload/', views.upload_story, name='upload_story'),

]
