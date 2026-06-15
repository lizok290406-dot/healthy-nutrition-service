from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class FoodCategory(models.Model):
    """Категория продуктов питания"""
    name = models.CharField(max_length=100, verbose_name='Название')
    icon = models.CharField(max_length=50, default='🥗', verbose_name='Иконка')
    color = models.CharField(max_length=7, default='#28a745', verbose_name='Цвет')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Категория продуктов'
        verbose_name_plural = 'Категории продуктов'
        ordering = ['name']

    def __str__(self):
        return self.name


class FoodItem(models.Model):
    """Продукт питания с нутриентами"""
    name = models.CharField(max_length=200, verbose_name='Название продукта')
    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.CASCADE,
        related_name='food_items',
        verbose_name='Категория'
    )
    calories = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='Калории (на 100г)'
    )
    proteins = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='Белки (г на 100г)'
    )
    carbohydrates = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='Углеводы (г на 100г)'
    )
    fats = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='Жиры (г на 100г)'
    )
    fiber = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Клетчатка (г на 100г)'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(
        upload_to='food_images/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    is_api_data = models.BooleanField(default=False, verbose_name='Данные из API')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def caloric_balance(self):
        """Определяет тип продукта по калорийности"""
        if self.calories < 100:
            return 'low'
        elif self.calories < 250:
            return 'medium'
        return 'high'


class UserProfile(models.Model):
    """Профиль пользователя с параметрами для расчёта нормы калорий"""
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    ACTIVITY_CHOICES = [
        ('sedentary', 'Сидячий образ жизни'),
        ('light', 'Лёгкая активность (1-3 дня/нед)'),
        ('moderate', 'Умеренная активность (3-5 дней/нед)'),
        ('active', 'Высокая активность (6-7 дней/нед)'),
        ('very_active', 'Очень высокая активность'),
    ]
    GOAL_CHOICES = [
        ('lose', 'Похудение'),
        ('maintain', 'Поддержание веса'),
        ('gain', 'Набор массы'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    age = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        null=True,
        blank=True,
        verbose_name='Возраст'
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='M',
        verbose_name='Пол'
    )
    weight = models.FloatField(
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        null=True,
        blank=True,
        verbose_name='Вес (кг)'
    )
    height = models.FloatField(
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        null=True,
        blank=True,
        verbose_name='Рост (см)'
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_CHOICES,
        default='moderate',
        verbose_name='Уровень активности'
    )
    goal = models.CharField(
        max_length=10,
        choices=GOAL_CHOICES,
        default='maintain',
        verbose_name='Цель'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль {self.user.username}'

    def calculate_bmr(self):
        """Расчёт базального метаболизма по формуле Миффлина-Сан Жеора"""
        if not all([self.weight, self.height, self.age]):
            return None
        if self.gender == 'M':
            return 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        return 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

    def calculate_tdee(self):
        """Расчёт суточной нормы калорий (TDEE)"""
        bmr = self.calculate_bmr()
        if bmr is None:
            return None
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        tdee = bmr * activity_multipliers.get(self.activity_level, 1.55)
        goal_adjustments = {
            'lose': -500,
            'maintain': 0,
            'gain': 500,
        }
        return round(tdee + goal_adjustments.get(self.goal, 0))

    def calculate_bmi(self):
        """Расчёт индекса массы тела"""
        if not all([self.weight, self.height]):
            return None
        height_m = self.height / 100
        return round(self.weight / (height_m ** 2), 1)

    def get_bmi_category(self):
        """Категория ИМТ"""
        bmi = self.calculate_bmi()
        if bmi is None:
            return None
        if bmi < 18.5:
            return ('Недостаточный вес', 'info')
        elif bmi < 25:
            return ('Нормальный вес', 'success')
        elif bmi < 30:
            return ('Избыточный вес', 'warning')
        return ('Ожирение', 'danger')


class MealLog(models.Model):
    """Дневник питания - запись о приёме пищи"""
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('snack', 'Перекус'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='meal_logs',
        verbose_name='Пользователь'
    )
    food_item = models.ForeignKey(
        FoodItem,
        on_delete=models.CASCADE,
        related_name='meal_logs',
        verbose_name='Продукт'
    )
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPE_CHOICES,
        default='breakfast',
        verbose_name='Тип приёма пищи'
    )
    amount = models.FloatField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество (г)'
    )
    date = models.DateField(default=timezone.now, verbose_name='Дата')
    notes = models.TextField(blank=True, verbose_name='Заметки')

    class Meta:
        verbose_name = 'Запись в дневнике'
        verbose_name_plural = 'Записи в дневнике'
        ordering = ['-date', 'meal_type']

    def __str__(self):
        return f'{self.user.username} - {self.food_item.name} ({self.date})'

    @property
    def total_calories(self):
        return round(self.food_item.calories * self.amount / 100, 1)

    @property
    def total_proteins(self):
        return round(self.food_item.proteins * self.amount / 100, 1)

    @property
    def total_carbohydrates(self):
        return round(self.food_item.carbohydrates * self.amount / 100, 1)

    @property
    def total_fats(self):
        return round(self.food_item.fats * self.amount / 100, 1)


class WeightLog(models.Model):
    """Дневник веса пользователя"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='weight_logs',
        verbose_name='Пользователь'
    )
    weight = models.FloatField(
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        verbose_name='Вес (кг)'
    )
    date = models.DateField(default=timezone.now, verbose_name='Дата')
    notes = models.TextField(blank=True, verbose_name='Заметки')

    class Meta:
        verbose_name = 'Запись веса'
        verbose_name_plural = 'Записи веса'
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f'{self.user.username} - {self.weight}кг ({self.date})'