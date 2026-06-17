from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from nutrition.models import UserProfile


def register_view(request):
    """Регистрация нового пользователя"""
    # Если уже вошёл — отправляем в дневник
    if request.user.is_authenticated:
        return redirect('nutrition:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически создаём профиль для нового пользователя
            UserProfile.objects.create(user=user)
            # Сразу входим после регистрации
            login(request, user)
            messages.success(
                request,
                f'🎉 Добро пожаловать, {user.username}! '
                f'Заполни профиль для расчёта нормы калорий.'
            )
            return redirect('users:profile')
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('nutrition:dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'👋 С возвращением, {user.username}!')
            # Если была страница откуда пришли — туда и возвращаем
            next_url = request.GET.get('next', 'nutrition:dashboard')
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Вы вышли из системы.')
    return redirect('nutrition:home')


@login_required
def profile_view(request):
    """Страница профиля пользователя"""
    # get_object_or_404 — если профиля нет, выдаст ошибку 404
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Обновляем имя и фамилию пользователя
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.save()
            messages.success(request, '✅ Профиль успешно обновлён!')
            return redirect('users:profile')
    else:
        form = ProfileUpdateForm(instance=profile)

    # Считаем показатели для отображения
    context = {
        'form': form,
        'profile': profile,
        'tdee': profile.calculate_tdee(),
        'bmi': profile.calculate_bmi(),
        'bmi_category': profile.get_bmi_category(),
    }
    return render(request, 'users/profile.html', context)