import requests
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, F, FloatField, ExpressionWrapper
from django.http import JsonResponse
from django.utils import timezone

from .models import Product, Category, DiaryEntry, UserProfile, BudgetPlan
from .forms import (
    DiaryEntryForm, BudgetForm, ProductSearchForm,
    UserProfileForm, RegisterForm, FoodItemForm
)


def home(request):
    """Главная страница"""
    today = timezone.now().date()
    context = {'today': today}

    if request.user.is_authenticated:
        entries_today = DiaryEntry.objects.filter(
            user=request.user,
            date=today
        ).select_related('product')

        totals = {
            'calories': sum(e.calories_consumed for e in entries_today),
            'protein': sum(e.protein_consumed for e in entries_today),
            'carbs': sum(e.carbs_consumed for e in entries_today),
            'fat': sum(e.fat_consumed for e in entries_today),
        }

        daily_goal = 2000
        try:
            profile = request.user.profile
            if profile.daily_calorie_goal:
                daily_goal = profile.daily_calorie_goal
        except UserProfile.DoesNotExist:
            pass

        calorie_percent = 0
        if daily_goal > 0:
            calorie_percent = min(
                round(totals['calories'] / daily_goal * 100, 1), 100
            )

        bmi = None
        bmi_category = ''
        try:
            prof = request.user.profile
            if prof.weight and prof.height:
                height_m = prof.height / 100
                bmi = round(prof.weight / (height_m ** 2), 1)
                if bmi < 18.5:
                    bmi_category = 'Недостаточный вес'
                elif bmi < 25:
                    bmi_category = 'Нормальный вес'
                elif bmi < 30:
                    bmi_category = 'Избыточный вес'
                else:
                    bmi_category = 'Ожирение'
        except UserProfile.DoesNotExist:
            pass

        chart_labels = []
        chart_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_entries = DiaryEntry.objects.filter(
                user=request.user, date=day
            ).select_related('product')
            day_calories = sum(e.calories_consumed for e in day_entries)
            chart_labels.append(day.strftime('%d.%m'))
            chart_data.append(round(day_calories, 1))

        budget_plan = BudgetPlan.objects.filter(
            user=request.user, date=today
        ).first()

        context.update({
            'totals': totals,
            'daily_goal': daily_goal,
            'calorie_percent': calorie_percent,
            'bmi': bmi,
            'bmi_category': bmi_category,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'budget_plan': budget_plan,
        })

    return render(request, 'nutrition/home.html', context)


def food_catalog(request):
    """
    Каталог продуктов.
    Поиск БЕЗ учёта регистра — icontains.
    яблоко = Яблоко = ЯБЛОКО = ЯбЛоКо
    """
    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    max_calories = request.GET.get('max_calories', '').strip()
    sort_by = request.GET.get('sort_by', '').strip()

    products = Product.objects.select_related('category').all()

    if query:
        products = products.filter(name__icontains=query)

    if selected_category:
        try:
            products = products.filter(
                category_id=int(selected_category)
            )
        except (ValueError, TypeError):
            pass

    if max_calories:
        try:
            products = products.filter(
                calories__lte=float(max_calories)
            )
        except (ValueError, TypeError):
            pass

    sort_map = {
        'name': 'name',
        'calories_asc': 'calories',
        'calories_desc': '-calories',
    }
    if sort_by in sort_map:
        products = products.order_by(sort_map[sort_by])

    all_categories = Category.objects.all()

    category_stats = Category.objects.annotate(
        count=Count('products'),
        avg_calories=Avg('products__calories')
    ).filter(count__gt=0)

    for cat in category_stats:
        cat.icon = cat.emoji

    return render(request, 'nutrition/food_catalog.html', {
        'foods': products,
        'query': query,
        'total_count': products.count(),
        'category_stats': category_stats,
        'all_categories': all_categories,
        'selected_category': selected_category,
        'max_calories': max_calories,
        'sort_by': sort_by,
    })


def food_detail(request, pk):
    """Страница отдельного продукта"""
    food = get_object_or_404(Product, pk=pk)
    return render(request, 'nutrition/food_detail.html', {'food': food})

def recommend(request):
    """Подбор продуктов: дёшево и полезно для студента.

    Считаем «белок на рубль» прямо в запросе к базе (F-объекты)
    и сортируем продукты от самых выгодных к менее выгодным.
    """
    max_calories = request.GET.get('max_calories', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    selected_category = request.GET.get('category', '').strip()

    # Берём только продукты, у которых указана цена больше нуля
    products = Product.objects.select_related('category').filter(
        price_per_100g__isnull=False,
        price_per_100g__gt=0,
    )

    if selected_category:
        try:
            products = products.filter(category_id=int(selected_category))
        except (ValueError, TypeError):
            pass

    if max_calories:
        try:
            products = products.filter(calories__lte=float(max_calories))
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            products = products.filter(price_per_100g__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    # F-объекты: база сама делит "белок / цена" для каждого продукта
    products = products.annotate(
        protein_per_ruble=ExpressionWrapper(
            F('protein') / F('price_per_100g'),
            output_field=FloatField(),
        )
    ).order_by('-protein_per_ruble')[:15]

    # Сколько калорий осталось на сегодня (если есть норма в профиле)
    remaining_calories = None
    if request.user.is_authenticated:
        try:
            goal = request.user.profile.daily_calorie_goal
        except UserProfile.DoesNotExist:
            goal = None
        if goal:
            today = timezone.now().date()
            entries = DiaryEntry.objects.filter(
                user=request.user, date=today
            ).select_related('product')
            consumed = sum(e.calories_consumed for e in entries)
            remaining_calories = round(goal - consumed)

    return render(request, 'nutrition/recommend.html', {
        'products': products,
        'all_categories': Category.objects.all(),
        'max_calories': max_calories,
        'max_price': max_price,
        'selected_category': selected_category,
        'remaining_calories': remaining_calories,
    })

@login_required
def dashboard(request):
    """Дневник питания"""
    today = timezone.now().date()

    entries = DiaryEntry.objects.filter(
        user=request.user,
        date=today
    ).select_related('product', 'product__category')

    meals = {
        'breakfast': {'name': 'Завтрак', 'emoji': '🌅', 'entries': []},
        'lunch': {'name': 'Обед', 'emoji': '☀️', 'entries': []},
        'dinner': {'name': 'Ужин', 'emoji': '🌙', 'entries': []},
        'snack': {'name': 'Перекус', 'emoji': '🍎', 'entries': []},
    }
    for entry in entries:
        if entry.meal_type in meals:
            meals[entry.meal_type]['entries'].append(entry)

    totals = {
        'calories': sum(e.calories_consumed for e in entries),
        'protein': sum(e.protein_consumed for e in entries),
        'carbs': sum(e.carbs_consumed for e in entries),
        'fat': sum(e.fat_consumed for e in entries),
    }

    daily_goal = 2000
    try:
        if request.user.profile.daily_calorie_goal:
            daily_goal = request.user.profile.daily_calorie_goal
    except UserProfile.DoesNotExist:
        pass

    calorie_percent = 0
    if daily_goal > 0:
        calorie_percent = min(
            round(totals['calories'] / daily_goal * 100, 1), 100
        )

    budget_plan = BudgetPlan.objects.filter(
        user=request.user, date=today
    ).first()

    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_entries = DiaryEntry.objects.filter(
            user=request.user, date=day
        ).select_related('product')
        day_calories = sum(e.calories_consumed for e in day_entries)
        chart_labels.append(day.strftime('%d.%m'))
        chart_data.append(round(day_calories, 1))

    bmi = None
    bmi_category = ''
    try:
        prof = request.user.profile
        if prof.weight and prof.height:
            height_m = prof.height / 100
            bmi = round(prof.weight / (height_m ** 2), 1)
            if bmi < 18.5:
                bmi_category = 'Недостаточный вес'
            elif bmi < 25:
                bmi_category = 'Нормальный вес'
            elif bmi < 30:
                bmi_category = 'Избыточный вес'
            else:
                bmi_category = 'Ожирение'
    except UserProfile.DoesNotExist:
        pass

    return render(request, 'nutrition/dashboard.html', {
        'entries': entries,
        'meals': meals,
        'totals': totals,
        'today': today,
        'daily_goal': daily_goal,
        'calorie_percent': calorie_percent,
        'budget_plan': budget_plan,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'bmi': bmi,
        'bmi_category': bmi_category,
    })


@login_required
def add_meal(request):
    """Добавление записи в дневник"""
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, 'Запись добавлена!')
            return redirect('nutrition:dashboard')
    else:
        form = DiaryEntryForm(initial={'date': timezone.now().date()})

    return render(request, 'nutrition/add_meal.html', {'form': form})


@login_required
def delete_meal(request, pk):
    """Удаление записи из дневника"""
    entry = get_object_or_404(DiaryEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Запись удалена!')
    return redirect('nutrition:dashboard')


@login_required
def add_food_item(request):
    """Добавление нового продукта в каталог через форму."""
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(
                request,
                f'Продукт «{product.name}» добавлен в каталог!'
            )
            return redirect('nutrition:food_catalog')
        messages.error(request, 'Проверьте правильность заполнения формы.')
    else:
        form = FoodItemForm(initial={
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'emoji': '🍽️',
        })

    return render(request, 'nutrition/add_food_item.html', {'form': form})


@login_required
def budget_view(request):
    """Страница управления бюджетом"""
    today = timezone.now().date()

    budget_plan = BudgetPlan.objects.filter(
        user=request.user, date=today
    ).first()

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget_plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            existing = BudgetPlan.objects.filter(
                user=request.user,
                date=plan.date
            ).first()
            if existing and (not plan.pk or existing.pk != plan.pk):
                existing.daily_budget = plan.daily_budget
                existing.save()
                messages.success(request, 'Бюджет обновлён!')
            else:
                plan.save()
                messages.success(request, 'Бюджет сохранён!')
            return redirect('nutrition:budget')
    else:
        form = BudgetForm(instance=budget_plan, initial={'date': today})

    week_budgets = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        plan = BudgetPlan.objects.filter(
            user=request.user, date=day
        ).first()

        entries_that_day = DiaryEntry.objects.filter(
            user=request.user,
            date=day,
            product__price_per_100g__isnull=False
        ).select_related('product')

        spent = round(sum(
            e.product.price_per_100g * e.amount_grams / 100
            for e in entries_that_day
        ), 2)

        week_budgets.append({
            'date': day,
            'budget': plan.daily_budget if plan else 0,
            'spent': spent,
            'within': (spent <= plan.daily_budget) if plan else None,
            'remaining': round(plan.daily_budget - spent, 2) if plan else 0,
        })

    return render(request, 'nutrition/budget.html', {
        'form': form,
        'budget_plan': budget_plan,
        'week_budgets': week_budgets,
        'today': today,
    })


@login_required
def progress(request):
    """Страница прогресса — графики за 30 дней"""
    today = timezone.now().date()
    labels = []
    calories_data = []

    all_calories = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        day_entries = DiaryEntry.objects.filter(
            user=request.user, date=day
        ).select_related('product')
        day_calories = sum(e.calories_consumed for e in day_entries)
        labels.append(day.strftime('%d.%m'))
        calories_data.append(round(day_calories, 1))
        if day_calories > 0:
            all_calories.append(day_calories)

    analytics = None
    if all_calories:
        analytics = {
            'avg_calories': round(sum(all_calories) / len(all_calories)),
            'max_calories': round(max(all_calories)),
            'min_calories': round(min(all_calories)),
            'days_tracked': len(all_calories),
        }

    daily_goal = 2000
    try:
        if request.user.profile.daily_calorie_goal:
            daily_goal = request.user.profile.daily_calorie_goal
    except UserProfile.DoesNotExist:
        pass

    total_entries = DiaryEntry.objects.filter(
        user=request.user
    ).count()

    return render(request, 'nutrition/progress.html', {
        'labels': labels,
        'calories_data': calories_data,
        'analytics': analytics,
        'daily_goal': daily_goal,
        'total_entries': total_entries,
        'today': today,
        'weekly_chart': True,
    })


def calorie_calculator(request):
    """Калькулятор калорий"""
    result = None

    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight', 0))
            height = float(request.POST.get('height', 0))
            age = int(request.POST.get('age', 0))
            gender = request.POST.get('gender', 'female')
            activity = request.POST.get('activity', 'moderate')
            goal = request.POST.get('goal', 'maintain')

            if gender == 'male':
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161

            multipliers = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very_active': 1.9,
            }
            tdee = bmr * multipliers.get(activity, 1.55)
            adjustments = {'lose': -500, 'maintain': 0, 'gain': 300}
            tdee += adjustments.get(goal, 0)

            result = {
                'bmr': round(bmr),
                'tdee': round(tdee),
                'protein': round(tdee * 0.3 / 4),
                'carbs': round(tdee * 0.4 / 4),
                'fat': round(tdee * 0.3 / 9),
            }

            if request.user.is_authenticated:
                profile, created = UserProfile.objects.get_or_create(
                    user=request.user
                )
                profile.weight = weight
                profile.height = height
                profile.age = age
                profile.gender = gender
                profile.goal = goal
                profile.activity_level = activity
                profile.daily_calorie_goal = tdee
                profile.save()
                messages.success(request, 'Норма калорий сохранена!')

        except (ValueError, TypeError):
            messages.error(request, 'Проверьте введённые данные')

    return render(request, 'nutrition/calorie_calculator.html', {
        'result': result
    })


@login_required
def log_weight(request):
    """Запись веса пользователя"""
    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight', 0))
            if weight > 0:
                profile, created = UserProfile.objects.get_or_create(
                    user=request.user
                )
                profile.weight = weight
                profile.save()
                messages.success(request, f'Вес {weight} кг сохранён!')
        except (ValueError, TypeError):
            messages.error(request, 'Введите корректный вес')
        return redirect('nutrition:progress')

    return render(request, 'nutrition/log_weight.html')


def api_search_food(request):
    """API поиск продуктов — сначала в БД, потом во внешнем API"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    local_results = Product.objects.filter(
        name__icontains=query
    ).select_related('category')[:5]

    if local_results.exists():
        results = [
            {
                'name': item.name,
                'calories': item.calories,
                'protein': item.protein,
                'carbs': item.carbs,
                'fat': item.fat,
            }
            for item in local_results
        ]
        return JsonResponse({'results': results, 'source': 'local'})

    try:
        url = 'https://world.openfoodfacts.org/cgi/search.pl'
        params = {
            'search_terms': query,
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 5,
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        products = data.get('products', [])

        results = []
        for p in products:
            nutriments = p.get('nutriments', {})
            cal = nutriments.get('energy-kcal_100g', 0)
            name = p.get('product_name', '').strip()
            if cal and name:
                results.append({
                    'name': name,
                    'calories': round(float(cal), 1),
                    'protein': round(
                        float(nutriments.get('proteins_100g', 0)), 1
                    ),
                    'carbs': round(
                        float(nutriments.get('carbohydrates_100g', 0)), 1
                    ),
                    'fat': round(
                        float(nutriments.get('fat_100g', 0)), 1
                    ),
                })

        return JsonResponse({'results': results[:5], 'source': 'api'})

    except Exception:
        return JsonResponse({'results': [], 'source': 'error'})