from django import forms
from .models import user_area_subscription

# this form lets users create or update their alert preferences
class user_area_subscription_form(forms.ModelForm):

    # this meta class tells django which model the form is based on
    class Meta:
        model = user_area_subscription

        # these are the fields the user can fill out
        fields = ['area', 'phone_number', 'notification_type']

        # form widgets
        widgets = {
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'enter area name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'notification_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
