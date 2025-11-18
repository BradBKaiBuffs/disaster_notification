from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserAreaSubscription


# lets users create or update their alert preferences
class UserAreaSubscriptionForm(forms.ModelForm):

    class Meta:
        model = UserAreaSubscription

        # these are the fields the user can fill out
        fields = ["area", "phone_number", "notification_type"]

        # widgets
        widgets = {
            "area": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "type area name",
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "+1234567890",
            }),
            "notification_type": forms.Select(attrs={
                "class": "form-control",
            }),
        }

# user creation form
# uses django built-in security for registration
class UserRegistrationForm(UserCreationForm):

    # require email
    email = forms.EmailField(required=True)

    class Meta:
        model = User

        # include username, email and password fields
        fields = ["username", "email", "password1", "password2"]

# upload form for csv files
class CsvUploadForm(forms.Form):

    # csv upload input
    file = forms.FileField(label="upload csv file")