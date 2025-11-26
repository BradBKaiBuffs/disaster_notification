from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserAreaSubscription


# lets users create or update their alert preferences with this form
class UserAreaSubscriptionForm(forms.ModelForm):

    class Meta:
        model = UserAreaSubscription

        fields = ["state", "county", "phone_number", "notification_type"]

        widgets = {
            # NO LONGER USED (area_desc no longer used)
            # "area": forms.TextInput(attrs={
            #     "class": "form-control",
            #     "placeholder": "Type area name",
            # }),
            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Type state name",
            }),
            "county": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Type county name",
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Type phone number",
            }),
            # NO LONGER USED (Vonage doesn't need it)
            # "carrier": forms.TextInput(attrs={
            #     "class": "form-control",
            #     "placeholder": "Type carrier"
            # }),
            "notification_type": forms.Select(attrs={
                "class": "form-control",
            }),
        }

# user creation form that uses django built-in security for registration
class UserRegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

# upload form for csv files from the admin site
class CsvUploadForm(forms.Form):
    file = forms.FileField(label="upload csv file")