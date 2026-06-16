from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import BudgetPlan, DiaryEntry, Product, UserProfile


class DiaryEntryForm(forms.ModelForm):
    """Форма добавления еды в дневник"""
    
    class Meta:
        model = DiaryEntry
        fields = ['product', 'meal_type', 'amount_grams', 'date']
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'product': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'meal_type': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'amount_grams': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'step': '1',
                    'placeholder': 'Например: 150'
                }
            ),
        }
        labels = {
            'product': 'Продукт',
            'meal_type': 'Приём пищи',
            'amount_grams': 'Количество (г)',
            'date': 'Дата',
        }


class BudgetForm(forms.ModelForm):
    """Форма установки дневного бюджета на питание"""
    
    class Meta:
        model = BudgetPlan
        fields = ['date', 'daily_budget']
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'daily_budget': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '10',
                    'placeholder': 'Например: 500'
                }
            ),
        }
        labels = {
            'date': 'Дата',
            'daily_budget': 'Дневной бюджет (₽)',
        }


class ProductSearchForm(forms.Form):
    """Форма поиска продуктов в каталоге"""
    
    q = forms.CharField(
        required=False,
        label='Поиск продукта',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: яблоко...',
            'autocomplete': 'off',
        })
    )
    category = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    max_calories = forms.FloatField(
        required=False,
        label='Макс. калорий',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Макс. калорий',
            'min': '0',
        })
    )
    sort = forms.ChoiceField(
        required=False,
        label='Сортировка',
        choices=[
            ('', '-- Сортировка'),
            ('name', 'По названию'),
            ('calories_asc', 'Калории ↑'),
            ('calories_desc', 'Калории ↓'),
            ('price_asc', 'Цена ↑'),
            ('price_desc', 'Цена ↓'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    class Meta:
        model = UserProfile
        fields = ['age', 'weight', 'height', 'gender', 'goal', 'activity_level']
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '10', 'max': '100'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '30', 'max': '300',
                'step': '0.1'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '100', 'max': '250',
                'step': '0.1'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'goal': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'age': 'Возраст',
            'weight': 'Вес (кг)',
            'height': 'Рост (см)',
            'gender': 'Пол',
            'goal': 'Цель',
            'activity_level': 'Уровень активности',
        }


class RegisterForm(UserCreationForm):
    """Форма регистрации нового пользователя"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

class FoodItemForm(forms.ModelForm):
    """Форма добавления нового продукта в каталог"""

    class Meta:
        model = Product
        fields = ['name', 'category', 'calories', 'protein',
                  'carbs', 'fat', 'emoji', 'price_per_100g']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Яблоко'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'calories': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'protein': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'carbs': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'emoji': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '🍎'
            }),
            'price_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.1',
                'placeholder': 'Например: 3.50'
            }),
        }
        labels = {
            'name': 'Название продукта',
            'category': 'Категория',
            'calories': 'Калории (на 100г)',
            'protein': 'Белки (на 100г)',
            'carbs': 'Углеводы (на 100г)',
            'fat': 'Жиры (на 100г)',
            'emoji': 'Эмодзи',
            'price_per_100g': 'Цена за 100г (₽)',
        }

class FoodItemForm(forms.ModelForm):
    """Форма добавления нового продукта в каталог"""

    class Meta:
        model = Product
        fields = ['name', 'category', 'calories', 'protein',
                  'carbs', 'fat', 'emoji', 'price_per_100g']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Яблоко'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'calories': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'protein': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'carbs': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'step': '0.1'
            }),
            'emoji': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '🍎'
            }),
            'price_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.1',
                'placeholder': 'Например: 3.50'
            }),
        }
        labels = {
            'name': 'Название продукта',
            'category': 'Категория',
            'calories': 'Калории (на 100г)',
            'protein': 'Белки (на 100г)',
            'carbs': 'Углеводы (на 100г)',
            'fat': 'Жиры (на 100г)',
            'emoji': 'Эмодзи',
            'price_per_100g': 'Цена за 100г (₽)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['emoji', 'protein', 'carbs', 'fat']:
            self.fields[field_name].required = False

    def clean_emoji(self):
        return self.cleaned_data.get('emoji') or '🍽️'

    def clean_protein(self):
        return self.cleaned_data.get('protein') or 0

    def clean_carbs(self):
        return self.cleaned_data.get('carbs') or 0

    def clean_fat(self):
        return self.cleaned_data.get('fat') or 0