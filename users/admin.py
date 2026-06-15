from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from nutrition.models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]


# Перерегистрируем User с нашим кастомным Admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)