from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    child_emails = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_child_emails(self):
        raw_emails = self.cleaned_data["child_emails"]
        emails = [e.strip() for e in raw_emails.split(",") if e.strip()]
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(f"Invalid child email: {email}")
        return emails

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class ParentRegistrationForm(forms.Form):
    parent_email = forms.EmailField()
    child_email = forms.EmailField()
