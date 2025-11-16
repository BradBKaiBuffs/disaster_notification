from django import forms
from .models import user_area_subscription
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# ets users create or update their alert preferences
class user_area_subscription_form(forms.ModelForm):

    # tells django which model the form is based on
    class Meta:
        model = user_area_subscription

        # these are the fields the user can fill out
        fields = ['area', 'phone_number', 'notification_type']

        # form widgets
        widgets = {
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'type area name',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'notification_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
# user creation form
# uses Django for account registration and security
class user_registration_form(UserCreationForm):
    # email
    email = forms.EmailField(required=True)
    # grabs username, email and password creation
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
