from django.contrib import admin
from .models import FoodCategory, FoodItem, MealLog, WeightLog, UserProfile


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color']
    search_fields = ['name']


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'calories', 'proteins',
                    'carbohydrates', 'fats', 'is_api_data']
    list_filter = ['category', 'is_api_data']
    search_fields = ['name', 'description']
    list_editable = ['calories']
    ordering = ['name']


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_item', 'meal_type', 'amount', 'date']
    list_filter = ['meal_type', 'date', 'user']
    search_fields = ['user__username', 'food_item__name']
    date_hierarchy = 'date'


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'weight', 'date']
    list_filter = ['user']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'gender', 'weight', 'height',
                    'activity_level', 'goal']
    list_filter = ['gender', 'activity_level', 'goal']
    search_fields = ['user__username', 'user__email']