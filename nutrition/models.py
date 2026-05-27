from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    ACTIVITY_CHOICES = [
        ('low', 'Низкая'),
        ('light', 'Лёгкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
    ]

    GOAL_CHOICES = [
        ('lose', 'Похудение'),
        ('maintain', 'Поддержание'),
        ('gain', 'Набор массы'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField()
    weight = models.FloatField()
    height = models.FloatField()
    activity_level = models.CharField(max_length=10, choices=ACTIVITY_CHOICES)
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES)
    daily_budget = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.user.username

    def get_bmr(self):
        if self.gender == 'male':
            return 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        return 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

    def get_activity_multiplier(self):
        multipliers = {
            'low': 1.2,
            'light': 1.375,
            'medium': 1.55,
            'high': 1.725,
        }
        return multipliers.get(self.activity_level, 1.2)

    def get_daily_calories(self):
        calories = self.get_bmr() * self.get_activity_multiplier()

        if self.goal == 'lose':
            calories *= 0.85
        elif self.goal == 'gain':
            calories *= 1.10

        return round(calories, 2)
    
    def get_target_proteins(self):
        return round((self.get_daily_calories() * 0.25) / 4, 2)

    def get_target_fats(self):
        return round((self.get_daily_calories() * 0.30) / 9, 2)

    def get_target_carbs(self):
        return round((self.get_daily_calories() * 0.45) / 4, 2)


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    calories_per_100g = models.FloatField()
    proteins_per_100g = models.FloatField()
    fats_per_100g = models.FloatField()
    carbs_per_100g = models.FloatField()
    price_per_100g = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


class Ration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rations')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Рацион {self.user.username} на {self.date}'

    def total_calories(self):
        total = 0
        for item in self.items.all():
            total += item.product.calories_per_100g / 100 * item.grams
        return round(total, 2)

    def total_proteins(self):
        total = 0
        for item in self.items.all():
            total += item.product.proteins_per_100g / 100 * item.grams
        return round(total, 2)

    def total_fats(self):
        total = 0
        for item in self.items.all():
            total += item.product.fats_per_100g / 100 * item.grams
        return round(total, 2)

    def total_carbs(self):
        total = 0
        for item in self.items.all():
            total += item.product.carbs_per_100g / 100 * item.grams
        return round(total, 2)

    def total_price(self):
        total = 0
        for item in self.items.all():
            total += float(item.product.price_per_100g) / 100 * item.grams
        return round(total, 2)
    
    def calorie_difference(self):
        profile = self.user.profile
        return round(self.total_calories() - profile.get_daily_calories(), 2)

    def is_within_budget(self):
        profile = self.user.profile
        return self.total_price() <= float(profile.daily_budget)
    
    def calorie_status(self):
        difference = self.calorie_difference()

        if difference < -100:
            return 'Дефицит калорий'
        elif difference > 100:
            return 'Избыток калорий'
        return 'Норма калорий'
    
    def calorie_status_class(self):
        status = self.calorie_status()

        if status == 'Норма калорий':
            return 'good'
        elif status == 'Дефицит калорий':
            return 'warning'
        return 'bad'
    
    def calorie_progress(self):
        profile = self.user.profile
        target = profile.get_daily_calories()

        if target == 0:
            return 0

        progress = (self.total_calories() / target) * 100

        if progress > 100:
            progress = 100

        return round(progress, 2)
    
    def proteins_difference(self):
        return round(self.total_proteins() - self.user.profile.get_target_proteins(), 2)

    def fats_difference(self):
        return round(self.total_fats() - self.user.profile.get_target_fats(), 2)

    def carbs_difference(self):
        return round(self.total_carbs() - self.user.profile.get_target_carbs(), 2)
    
    def recommendation(self):
        messages = []

        if self.calorie_difference() < -100:
            messages.append('Рацион содержит дефицит калорий.')
        elif self.calorie_difference() > 100:
            messages.append('Рацион содержит избыток калорий.')
        else:
            messages.append('Рацион близок к норме по калориям.')

        if self.proteins_difference() < -10:
            messages.append('Рекомендуется увеличить количество белковых продуктов.')
        elif self.proteins_difference() > 10:
            messages.append('Наблюдается избыток белка.')

        if self.fats_difference() < -10:
            messages.append('Рацион содержит недостаток жиров.')
        elif self.fats_difference() > 10:
            messages.append('Рацион содержит избыток жиров.')

        if self.carbs_difference() < -15:
            messages.append('Рацион содержит недостаток углеводов.')
        elif self.carbs_difference() > 15:
            messages.append('Рацион содержит избыток углеводов.')

        if self.is_within_budget():
            messages.append('Рацион укладывается в установленный бюджет.')
        else:
            messages.append('Рацион превышает установленный бюджет.')

        return ' '.join(messages)
    
    def suggested_products(self):
        suggestions = []

        if self.proteins_difference() < -10:
            protein_products = Product.objects.filter(
                category__name__in=['Мясо', 'Рыба', 'Молочные продукты', 'Яйца', 'Бобовые']
            ).order_by('-proteins_per_100g', 'price_per_100g')[:4]

            suggestions.append({
                'title': 'Для восполнения белка',
                'items': protein_products
            })

        if self.carbs_difference() < -15:
            carb_products = Product.objects.filter(
                category__name__in=['Крупы', 'Фрукты', 'Бобовые']
            ).order_by('-carbs_per_100g', 'price_per_100g')[:4]

            suggestions.append({
                'title': 'Для восполнения углеводов',
                'items': carb_products
            })

        if self.fats_difference() < -10:
            fat_products = Product.objects.filter(
                category__name__in=['Орехи', 'Рыба', 'Молочные продукты']
            ).order_by('-fats_per_100g', 'price_per_100g')[:4]

            suggestions.append({
                'title': 'Для восполнения жиров',
                'items': fat_products
            })

        return suggestions    
    
    def budget_suggested_products(self):
        suggestions = []

        if self.proteins_difference() < -10:
            protein_products = Product.objects.filter(
                category__name__in=['Мясо', 'Рыба', 'Молочные продукты', 'Яйца', 'Бобовые']
            ).order_by('price_per_100g', '-proteins_per_100g')[:4]

            suggestions.append({
                'title': 'Бюджетные источники белка',
                'items': protein_products
            })

        if self.carbs_difference() < -15:
            carb_products = Product.objects.filter(
                category__name__in=['Крупы', 'Фрукты', 'Бобовые']
            ).order_by('price_per_100g', '-carbs_per_100g')[:4]

            suggestions.append({
                'title': 'Бюджетные источники углеводов',
                'items': carb_products
            })

        if self.fats_difference() < -10:
            fat_products = Product.objects.filter(
                category__name__in=['Орехи', 'Рыба', 'Молочные продукты']
            ).order_by('price_per_100g', '-fats_per_100g')[:4]

            suggestions.append({
                'title': 'Бюджетные источники жиров',
                'items': fat_products
            })

        return suggestions
    


class RationItem(models.Model):
    ration = models.ForeignKey(Ration, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    grams = models.FloatField()

    def __str__(self):
        return f'{self.product.name} - {self.grams} г'