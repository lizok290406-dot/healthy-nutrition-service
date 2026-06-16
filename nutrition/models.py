from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """Категория продуктов — например Фрукты, Овощи, Мясо"""
    name = models.CharField(max_length=100, verbose_name='Название')
    emoji = models.CharField(max_length=10, default='🍽️', verbose_name='Эмодзи')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Продукт питания — например Яблоко, Курица, Гречка"""
    name = models.CharField(max_length=200, verbose_name='Название')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория'
    )
    calories = models.FloatField(verbose_name='Калории на 100г')
    protein = models.FloatField(default=0, verbose_name='Белки на 100г')
    carbs = models.FloatField(default=0, verbose_name='Углеводы на 100г')
    fat = models.FloatField(default=0, verbose_name='Жиры на 100г')
    emoji = models.CharField(max_length=10, default='🍽️', verbose_name='Эмодзи')
    # Цена за 100г в рублях — нужна для расчёта бюджета
    price_per_100g = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Цена за 100г (руб.)'
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Профиль пользователя — хранит параметры для расчёта калорий"""
    
    GOAL_CHOICES = [
        ('lose', 'Похудение'),
        ('maintain', 'Поддержание веса'),
        ('gain', 'Набор массы'),
    ]
    
    ACTIVITY_CHOICES = [
        ('sedentary', 'Малоподвижный'),
        ('light', 'Лёгкая активность'),
        ('moderate', 'Умеренная активность'),
        ('active', 'Высокая активность'),
        ('very_active', 'Очень высокая активность'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name='Возраст')
    weight = models.FloatField(null=True, blank=True, verbose_name='Вес (кг)')
    height = models.FloatField(null=True, blank=True, verbose_name='Рост (см)')
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Мужской'), ('female', 'Женский')],
        default='female',
        verbose_name='Пол'
    )
    goal = models.CharField(
        max_length=20,
        choices=GOAL_CHOICES,
        default='maintain',
        verbose_name='Цель'
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_CHOICES,
        default='moderate',
        verbose_name='Уровень активности'
    )
    daily_calorie_goal = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Дневная норма калорий'
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def calculate_bmr(self):
        """Базовый обмен веществ по формуле Миффлина-Сан Жеора"""
        if not all([self.weight, self.height, self.age]):
            return 0
        if self.gender == 'male':
            return 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        return 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

    def calculate_tdee(self):
        """Суточная потребность в калориях с учётом активности и цели"""
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        bmr = self.calculate_bmr()
        tdee = bmr * multipliers.get(self.activity_level, 1.55)
        adjustments = {'lose': -500, 'maintain': 0, 'gain': 300}
        return round(tdee + adjustments.get(self.goal, 0), 0)

    def __str__(self):
        return f'Профиль {self.user.username}'


class DiaryEntry(models.Model):
    """Запись в дневнике питания — что съел пользователь и когда"""
    
    MEAL_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('snack', 'Перекус'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='diary_entries',
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='diary_entries',
        verbose_name='Продукт'
    )
    date = models.DateField(default=timezone.now, verbose_name='Дата')
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_CHOICES,
        default='breakfast',
        verbose_name='Приём пищи'
    )
    amount_grams = models.FloatField(verbose_name='Количество (г)')

    class Meta:
        verbose_name = 'Запись дневника'
        verbose_name_plural = 'Записи дневника'
        ordering = ['-date', 'meal_type']

    @property
    def calories_consumed(self):
        """Калории в этой порции"""
        return round(self.product.calories * self.amount_grams / 100, 1)

    @property
    def protein_consumed(self):
        """Белки в этой порции"""
        return round(self.product.protein * self.amount_grams / 100, 1)

    @property
    def carbs_consumed(self):
        """Углеводы в этой порции"""
        return round(self.product.carbs * self.amount_grams / 100, 1)

    @property
    def fat_consumed(self):
        """Жиры в этой порции"""
        return round(self.product.fat * self.amount_grams / 100, 1)

    @property
    def cost(self):
        """Стоимость этой порции в рублях"""
        if self.product.price_per_100g:
            return round(self.product.price_per_100g * self.amount_grams / 100, 2)
        return None

    def __str__(self):
        return f'{self.user.username} — {self.product.name} ({self.date})'


class BudgetPlan(models.Model):
    """Бюджет питания — сколько пользователь готов потратить на еду за день"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budget_plans',
        verbose_name='Пользователь'
    )
    date = models.DateField(default=timezone.now, verbose_name='Дата')
    daily_budget = models.FloatField(verbose_name='Дневной бюджет (руб.)')

    class Meta:
        verbose_name = 'Бюджет питания'
        verbose_name_plural = 'Бюджеты питания'
        # Один бюджет на пользователя на один день
        unique_together = ['user', 'date']

    def get_spent(self):
        """Считаем сколько потрачено за этот день"""
        entries = DiaryEntry.objects.filter(
            user=self.user,
            date=self.date,
            product__price_per_100g__isnull=False
        )
        total = sum(
            entry.product.price_per_100g * entry.amount_grams / 100
            for entry in entries
        )
        return round(total, 2)

    def get_remaining(self):
        """Сколько осталось денег"""
        return round(self.daily_budget - self.get_spent(), 2)

    def is_within_budget(self):
        """Уложился ли пользователь в бюджет"""
        return self.get_spent() <= self.daily_budget

    def get_percent_spent(self):
        """Процент потраченного бюджета"""
        if self.daily_budget == 0:
            return 0
        percent = self.get_spent() / self.daily_budget * 100
        return min(round(percent, 1), 100)

    def __str__(self):
        return f'Бюджет {self.user.username} на {self.date}'