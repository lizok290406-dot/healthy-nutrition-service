import json
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from plotly.utils import PlotlyJSONEncoder

from .forms import FoodItemForm, FoodSearchForm, MealLogForm, WeightLogForm
from .models import FoodCategory, FoodItem, MealLog, UserProfile, WeightLog


def home(request):
    categories = FoodCategory.objects.annotate(
        items_count=Count('food_items')
    ).order_by('-items_count')[:6]

    top_foods = FoodItem.objects.select_related('category').order_by('calories')[:8]

    stats = {
        'total_foods': FoodItem.objects.count(),
        'total_categories': FoodCategory.objects.count(),
        'total_users': UserProfile.objects.count(),
    }

    context = {
        'categories': categories,
        'top_foods': top_foods,
        'stats': stats,
    }
    return render(request, 'nutrition/home.html', context)


@login_required
def dashboard(request):
    today = date.today()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    today_logs = MealLog.objects.filter(
        user=request.user,
        date=today
    ).select_related('food_item', 'food_item__category')

    daily_totals = today_logs.aggregate(
        total_calories=Sum(F('food_item__calories') * F('amount') / 100),
        total_proteins=Sum(F('food_item__proteins') * F('amount') / 100),
        total_carbohydrates=Sum(F('food_item__carbohydrates') * F('amount') / 100),
        total_fats=Sum(F('food_item__fats') * F('amount') / 100),
    )

    tdee = profile.calculate_tdee()
    bmi = profile.calculate_bmi()
    bmi_category = profile.get_bmi_category()

    calories_consumed = round(daily_totals['total_calories'] or 0, 1)
    calories_progress = 0
    if tdee and tdee > 0:
        calories_progress = min(round((calories_consumed / tdee) * 100), 100)

    calories_chart = _get_weekly_calories_chart(request.user)

    context = {
        'profile': profile,
        'today_logs': today_logs,
        'daily_totals': daily_totals,
        'tdee': tdee,
        'bmi': bmi,
        'bmi_category': bmi_category,
        'calories_consumed': calories_consumed,
        'calories_progress': calories_progress,
        'calories_chart': calories_chart,
        'today': today,
        'macros_chart': None,  # график пока убираем, чтобы ничего не ехало
    }
    return render(request, 'nutrition/dashboard.html', context)


def _get_weekly_calories_chart(user):
    today = date.today()
    dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    calories_data = []
    for d in dates:
        total = MealLog.objects.filter(
            user=user,
            date=d
        ).aggregate(
            total=Sum(F('food_item__calories') * F('amount') / 100)
        )['total'] or 0
        calories_data.append(round(total, 1))

    date_labels = [d.strftime('%d.%m') for d in dates]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=date_labels,
        y=calories_data,
        marker=dict(color='rgba(102,126,234,0.8)'),
        text=calories_data,
        textposition='outside',
        name='Калории',
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#6c757d', size=12),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        height=250,
        showlegend=False,
    )

    return json.dumps(fig, cls=PlotlyJSONEncoder)


@login_required
def add_meal(request):
    if request.method == 'POST':
        form = MealLogForm(request.POST)
        if form.is_valid():
            meal_log = form.save(commit=False)
            meal_log.user = request.user
            meal_log.save()
            messages.success(request, f'Продукт «{meal_log.food_item.name}» добавлен в дневник!')
            return redirect('nutrition:dashboard')
    else:
        form = MealLogForm()

    return render(request, 'nutrition/add_meal.html', {'form': form})


@login_required
def delete_meal(request, pk):
    meal_log = get_object_or_404(MealLog, pk=pk, user=request.user)
    if request.method == 'POST':
        food_name = meal_log.food_item.name
        meal_log.delete()
        messages.success(request, f'Запись о «{food_name}» удалена.')
    return redirect('nutrition:dashboard')


@login_required
def log_weight(request):
    if request.method == 'POST':
        form = WeightLogForm(request.POST)
        if form.is_valid():
            weight_log = form.save(commit=False)
            weight_log.user = request.user

            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.weight = weight_log.weight
            profile.save()

            WeightLog.objects.update_or_create(
                user=request.user,
                date=weight_log.date,
                defaults={
                    'weight': weight_log.weight,
                    'notes': weight_log.notes
                }
            )
            messages.success(request, f'Вес {weight_log.weight} кг сохранён!')
            return redirect('nutrition:progress')
    else:
        form = WeightLogForm()

    return render(request, 'nutrition/log_weight.html', {'form': form})


@login_required
def progress(request):
    weight_logs = WeightLog.objects.filter(
        user=request.user
    ).order_by('date').values('date', 'weight', 'notes')

    weight_chart = None
    if weight_logs.exists():
        df = pd.DataFrame(list(weight_logs))
        df['date_str'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date_str'],
            y=df['weight'],
            mode='lines+markers',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#764ba2'),
            name='Вес',
        ))

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#6c757d', size=12),
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(
                gridcolor='rgba(0,0,0,0.05)',
                title='Дата',
                type='category',
            ),
            yaxis=dict(
                gridcolor='rgba(0,0,0,0.05)',
                title='Вес (кг)',
            ),
            height=350,
            showlegend=False,
        )
        weight_chart = json.dumps(fig, cls=PlotlyJSONEncoder)

    thirty_days_ago = date.today() - timedelta(days=30)
    meal_data = MealLog.objects.filter(
        user=request.user,
        date__gte=thirty_days_ago
    ).values('date', 'food_item__calories', 'amount')

    analytics = {}
    weekly_chart = None

    if meal_data.exists():
        df = pd.DataFrame(list(meal_data))
        df['total_cal'] = df['food_item__calories'] * df['amount'] / 100
        daily = df.groupby('date')['total_cal'].sum()

        analytics = {
            'avg_calories': round(daily.mean(), 1),
            'max_calories': round(daily.max(), 1),
            'min_calories': round(daily.min(), 1),
            'days_tracked': len(daily),
        }

        date_labels = [
            d.strftime('%d.%m') if hasattr(d, 'strftime') else str(d)
            for d in daily.index
        ]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=date_labels,
            y=daily.values.tolist(),
            mode='lines+markers',
            line=dict(color='#f6d365', width=2),
            marker=dict(size=5, color='#fda085'),
            fill='tozeroy',
            fillcolor='rgba(246,211,101,0.15)',
        ))

        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#6c757d', size=11),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            showlegend=False,
            xaxis=dict(type='category'),
        )
        weekly_chart = json.dumps(fig2, cls=PlotlyJSONEncoder)

    context = {
        'weight_logs': list(weight_logs[:10]),
        'weight_chart': weight_chart,
        'weekly_chart': weekly_chart,
        'analytics': analytics,
    }
    return render(request, 'nutrition/progress.html', context)


def food_catalog(request):
    form = FoodSearchForm(request.GET or None)
    foods = FoodItem.objects.select_related('category').all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        max_calories = form.cleaned_data.get('max_calories')
        sort_by = form.cleaned_data.get('sort_by')

        if query:
            foods = foods.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        if category:
            foods = foods.filter(category=category)
        if max_calories:
            foods = foods.filter(calories__lte=max_calories)
        if sort_by:
            foods = foods.order_by(sort_by)

    category_stats = FoodCategory.objects.annotate(
        avg_calories=Avg('food_items__calories'),
        count=Count('food_items')
    ).filter(count__gt=0)

    context = {
        'foods': foods,
        'form': form,
        'category_stats': category_stats,
        'total_count': foods.count(),
    }
    return render(request, 'nutrition/food_catalog.html', context)


def food_detail(request, pk):
    food = get_object_or_404(FoodItem, pk=pk)

    fig = go.Figure(data=[go.Bar(
        x=['Белки', 'Углеводы', 'Жиры', 'Клетчатка'],
        y=[food.proteins, food.carbohydrates, food.fats, food.fiber],
        marker=dict(color=['#667eea', '#f6d365', '#f093fb', '#4facfe']),
        text=[f'{v}г' for v in [food.proteins, food.carbohydrates, food.fats, food.fiber]],
        textposition='outside',
    )])

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#6c757d', size=12),
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        showlegend=False,
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)', title='г на 100г'),
    )

    nutrients_chart = json.dumps(fig, cls=PlotlyJSONEncoder)

    similar_foods = FoodItem.objects.filter(
        category=food.category
    ).exclude(pk=pk)[:4]

    context = {
        'food': food,
        'nutrients_chart': nutrients_chart,
        'similar_foods': similar_foods,
    }
    return render(request, 'nutrition/food_detail.html', context)


def search_food_api(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': [], 'error': 'Слишком короткий запрос'})

    app_id = settings.NUTRITIONIX_APP_ID
    api_key = settings.NUTRITIONIX_API_KEY

    if not app_id or not api_key:
        demo_data = _get_demo_nutrition_data(query)
        return JsonResponse({'results': demo_data, 'source': 'demo'})

    try:
        url = 'https://trackapi.nutritionix.com/v2/search/instant'
        headers = {
            'x-app-id': app_id,
            'x-app-key': api_key,
        }
        params = {'query': query, 'detailed': True}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get('common', [])[:5]:
            results.append({
                'name': item.get('food_name', ''),
                'photo': item.get('photo', {}).get('thumb', ''),
                'calories': item.get('nf_calories', 0),
            })
        return JsonResponse({'results': results, 'source': 'api'})

    except requests.RequestException:
        demo_data = _get_demo_nutrition_data(query)
        return JsonResponse({'results': demo_data, 'source': 'demo'})


def _get_demo_nutrition_data(query):
    demo_foods = [
        {'name': 'Яблоко', 'calories': 52, 'photo': ''},
        {'name': 'Банан', 'calories': 89, 'photo': ''},
        {'name': 'Куриная грудка', 'calories': 165, 'photo': ''},
        {'name': 'Гречка', 'calories': 343, 'photo': ''},
        {'name': 'Творог 5%', 'calories': 121, 'photo': ''},
        {'name': 'Авокадо', 'calories': 160, 'photo': ''},
        {'name': 'Лосось', 'calories': 208, 'photo': ''},
        {'name': 'Брокколи', 'calories': 34, 'photo': ''},
    ]
    return [f for f in demo_foods if query.lower() in f['name'].lower()]


@login_required
def calorie_calculator(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    result = None

    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight', profile.weight or 70))
            height = float(request.POST.get('height', profile.height or 170))
            age = int(request.POST.get('age', profile.age or 25))
            gender = request.POST.get('gender', profile.gender or 'M')
            activity = request.POST.get('activity', profile.activity_level or 'moderate')
            goal = request.POST.get('goal', profile.goal or 'maintain')

            if gender == 'M':
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
            adjustments = {'lose': -500, 'maintain': 0, 'gain': 500}
            final_calories = round(tdee + adjustments.get(goal, 0))

            result = {
                'bmr': round(bmr),
                'tdee': round(tdee),
                'target': final_calories,
                'proteins': round(final_calories * 0.3 / 4),
                'carbs': round(final_calories * 0.45 / 4),
                'fats': round(final_calories * 0.25 / 9),
            }
        except (ValueError, TypeError):
            messages.error(request, 'Проверьте корректность введённых данных.')

    context = {
        'profile': profile,
        'result': result,
    }
    return render(request, 'calorie_calculator.html', context)


@login_required
def add_food_item(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        if form.is_valid():
            food = form.save()
            messages.success(request, f'Продукт «{food.name}» добавлен в каталог!')
            return redirect('nutrition:food_detail', pk=food.pk)
    else:
        form = FoodItemForm()

    return render(request, 'nutrition/add_food_item.html', {'form': form})