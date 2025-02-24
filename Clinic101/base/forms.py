from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','title','first_name','last_name','password1','password2']
    

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['idCard','phone','address','birthDate','gender','weight','height','bloodType','ud','image','allergic','ud_symptoms','allergic_symptoms']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','title','first_name', 'last_name', 'email',]
        
        
       