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
    class Meta:
        model = UserProfile
        fields = [
            'age',
            'gender',
            'weight',
            'height',
            'activity_level',
            'goal',
            'daily_calorie_goal',
        ]

        labels = {
            'age': 'Возраст',
            'gender': 'Пол',
            'weight': 'Вес',
            'height': 'Рост',
            'activity_level': 'Уровень активности',
            'goal': 'Цель',
            'daily_calorie_goal': 'Дневная норма калорий',
        }

        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Возраст'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '1',
                'placeholder': 'Вес в кг'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '1',
                'placeholder': 'Рост в см'
            }),
            'activity_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'goal': forms.Select(attrs={
                'class': 'form-control'
            }),
            'daily_calorie_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
                'placeholder': 'Например, 2000'
            }),
        }