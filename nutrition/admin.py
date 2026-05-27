from django.contrib import admin
from .models import Profile, Category, Product, Ration, RationItem


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'gender',
        'age',
        'weight',
        'height',
        'activity_level',
        'goal',
        'daily_budget',
    )
    search_fields = ('user__username',)
    list_filter = ('gender', 'activity_level', 'goal')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'calories_per_100g',
        'proteins_per_100g',
        'fats_per_100g',
        'carbs_per_100g',
        'price_per_100g',
    )
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
    ordering = ('name',)


@admin.register(Ration)
class RationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'date',
        'total_calories',
        'total_price',
        'calorie_status',
        'is_within_budget',
    )
    search_fields = ('user__username',)
    list_filter = ('date', 'user')

    def total_calories(self, obj):
        return round(obj.total_calories(), 2)
    total_calories.short_description = 'Калории'

    def total_price(self, obj):
        return round(obj.total_price(), 2)
    total_price.short_description = 'Стоимость'

    def calorie_status(self, obj):
        return obj.calorie_status()
    calorie_status.short_description = 'Статус'

    def is_within_budget(self, obj):
        return 'Да' if obj.is_within_budget() else 'Нет'
    is_within_budget.short_description = 'В бюджете'


@admin.register(RationItem)
class RationItemAdmin(admin.ModelAdmin):
    list_display = ('ration', 'product', 'grams')
    search_fields = ('product__name', 'ration__user__username')
    list_filter = ('product__category', 'ration__date')