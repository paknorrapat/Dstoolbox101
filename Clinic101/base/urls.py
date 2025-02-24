from django.urls import path,include
from .views import *
from django.contrib.auth.views import PasswordResetView,PasswordResetDoneView,PasswordResetConfirmView,PasswordResetCompleteView



urlpatterns = [
    path("",firstpage,name='firstpage'),
    path("login/",login,name="login"),
    path("logout/",logout,name="logout"),
    path("register/",register,name="register"),
    path("profile_form/<int:user_id>",profile,name='profile-form'),

    path('password_reset/',PasswordResetView.as_view(template_name="registration/password_reset_form.html"),name="password_reset"),
    path('password_reset/done/',PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),name="password_reset_done"),
    path('reset/<uidb64>/<token>/',PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),name="password_reset_confirm"),
    path('reset/done/',PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),name="password_reset_complete"),

    path('profile/<int:user_id>/', showprofile, name='profile'), 
    path('update_profile/<int:user_id>/', updateprofile, name='update-profile'), 
    
]
