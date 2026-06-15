from django import forms
from .models import MealLog, WeightLog, FoodItem, FoodCategory


class MealLogForm(forms.ModelForm):
    class Meta:
        model = MealLog
        fields = ['food_item', 'meal_type', 'amount', 'date', 'notes']
        widgets = {
            'food_item': forms.Select(attrs={
                'class': 'form-select',
                'id': 'food-select',
            }),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100',
                'min': '1',
                'step': '0.1',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Необязательные заметки...',
            }),
        }
        labels = {
            'food_item': 'Продукт',
            'meal_type': 'Приём пищи',
            'amount': 'Количество (г)',
            'date': 'Дата',
            'notes': 'Заметки',
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Количество должно быть больше 0.')
        if amount and amount > 5000:
            raise forms.ValidationError('Количество не может превышать 5000г.')
        return amount


class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['weight', 'date', 'notes']
        widgets = {
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '70.5',
                'step': '0.1',
                'min': '20',
                'max': '300',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Заметки...',
            }),
        }
        labels = {
            'weight': 'Вес (кг)',
            'date': 'Дата',
            'notes': 'Заметки',
        }


class FoodSearchForm(forms.Form):
    SORT_CHOICES = [
        ('name', 'По названию (А-Я)'),
        ('calories', 'По калориям (возр.)'),
        ('-calories', 'По калориям (убыв.)'),
        ('proteins', 'По белкам'),
    ]

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '🔍 Поиск продукта...',
        }),
        label='Поиск',
    )
    category = forms.ModelChoiceField(
        queryset=FoodCategory.objects.all(),
        required=False,
        empty_label='Все категории',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Категория',
    )
    max_calories = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Макс. калорий',
        }),
        label='Макс. калорий',
    )
    sort_by = forms.ChoiceField(
        choices=[('', '-- Сортировка --')] + SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Сортировка',
    )


class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'category', 'calories', 'proteins',
                  'carbohydrates', 'fats', 'fiber', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'calories': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': '0'
            }),
            'proteins': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': '0'
            }),
            'carbohydrates': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': '0'
            }),
            'fats': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': '0'
            }),
            'fiber': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }