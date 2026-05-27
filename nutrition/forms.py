from django import forms
from .models import RationItem, Product, Profile, Ration


class RationItemForm(forms.ModelForm):
    class Meta:
        model = RationItem
        fields = ['product', 'grams']

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label='Продукт'
    )

    grams = forms.FloatField(label='Граммы')

    def clean_grams(self):
        grams = self.cleaned_data['grams']
        if grams <= 0:
            raise forms.ValidationError('Количество граммов должно быть больше 0.')
        return grams


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'gender',
            'age',
            'weight',
            'height',
            'activity_level',
            'goal',
            'daily_budget',
        ]
        labels = {
            'gender': 'Пол',
            'age': 'Возраст',
            'weight': 'Вес',
            'height': 'Рост',
            'activity_level': 'Уровень активности',
            'goal': 'Цель',
            'daily_budget': 'Дневной бюджет',
        }

    def clean_age(self):
        age = self.cleaned_data['age']
        if age <= 0:
            raise forms.ValidationError('Возраст должен быть больше 0.')
        return age

    def clean_weight(self):
        weight = self.cleaned_data['weight']
        if weight <= 0:
            raise forms.ValidationError('Вес должен быть больше 0.')
        return weight

    def clean_height(self):
        height = self.cleaned_data['height']
        if height <= 0:
            raise forms.ValidationError('Рост должен быть больше 0.')
        return height

    def clean_daily_budget(self):
        daily_budget = self.cleaned_data['daily_budget']
        if daily_budget < 0:
            raise forms.ValidationError('Бюджет не может быть отрицательным.')
        return daily_budget


class RationForm(forms.ModelForm):
    class Meta:
        model = Ration
        fields = ['date']
        labels = {
            'date': 'Дата рациона',
        }

    date = forms.DateField(
        label='Дата рациона',
        widget=forms.DateInput(attrs={'type': 'date'})
    )