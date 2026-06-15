from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from nutrition.models import UserProfile


class RegisterForm(UserCreationForm):
    """Форма регистрации"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        }),
        label='Email'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте логин',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль',
        })
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'


class LoginForm(AuthenticationForm):
    """Форма входа"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Логин',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль',
        })
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'


class ProfileUpdateForm(forms.ModelForm):
    """Форма обновления профиля"""
    class Meta:
        model = UserProfile
        fields = [
            'age', 'gender', 'weight', 'height',
            'activity_level', 'goal', 'avatar'
        ]
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 10,
                'max': 120,
                'placeholder': '25'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': 20,
                'max': 300,
                'placeholder': '70.0'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': 100,
                'max': 250,
                'placeholder': '170.0'
            }),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'goal': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'age': 'Возраст',
            'gender': 'Пол',
            'weight': 'Вес (кг)',
            'height': 'Рост (см)',
            'activity_level': 'Уровень активности',
            'goal': 'Ваша цель',
            'avatar': 'Фото профиля',
        }