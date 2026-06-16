from django.contrib import admin
from .models import Category, Product, DiaryEntry, UserProfile, BudgetPlan


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'description']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'calories',
        'protein', 'carbs', 'fat', 'price_per_100g'
    ]
    search_fields = ['name']
    list_filter = ['category']
    list_editable = ['price_per_100g']


@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'date', 'meal_type', 'amount_grams']
    search_fields = ['user__username', 'product__name']
    list_filter = ['meal_type', 'date']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'age', 'weight', 'height',
        'gender', 'goal', 'activity_level', 'daily_calorie_goal'
    ]
    search_fields = ['user__username']


@admin.register(BudgetPlan)
class BudgetPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'daily_budget']
    search_fields = ['user__username']
    list_filter = ['date']