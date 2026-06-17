from django.contrib import admin
from .models import Category, Product, UserProfile, DiaryEntry, BudgetPlan


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'emoji')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'calories',
                    'protein', 'carbs', 'fat', 'price_per_100g')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'weight', 'height',
                    'goal', 'daily_calorie_goal')
    list_filter = ('goal', 'gender')
    search_fields = ('user__username',)


@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'date', 'meal_type', 'amount_grams')
    list_filter = ('date', 'meal_type')
    search_fields = ('user__username', 'product__name')


@admin.register(BudgetPlan)
class BudgetPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'daily_budget')
    list_filter = ('date',)
    search_fields = ('user__username',)