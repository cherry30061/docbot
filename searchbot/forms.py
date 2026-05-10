"""Forms for signup, login, and document upload."""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.conf import settings
from .models import Document
from .utils.extractors import SUPPORTED_EXTENSIONS, get_file_extension


class SignupForm(UserCreationForm):
    """Custom signup form with email and role choice."""
    email = forms.EmailField(required=True)

    ROLE_CHOICES = (
        ('user', 'Normal User'),
        ('admin', 'Admin'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='user')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(AuthenticationForm):
    """Login form with Bootstrap styling."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class DocumentUploadForm(forms.ModelForm):
    """Document upload form with file validation."""
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a title for this document'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx,.xlsx,.pptx,.txt'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError("Please select a file.")

        # Check size: 2 MB limit (per Step 3 requirement)
        max_size = settings.MAX_UPLOAD_SIZE
        if file.size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(f"File too large. Max size is {size_mb} MB.")

        # Check extension
        ext = get_file_extension(file.name)
        if ext not in SUPPORTED_EXTENSIONS:
            raise forms.ValidationError(
                f"Unsupported file type '.{ext}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        return file
