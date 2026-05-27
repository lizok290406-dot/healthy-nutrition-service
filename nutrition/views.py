import pandas as pd
import plotly.express as px

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, RationForm, RationItemForm, RegisterForm
from .models import Category, Product, Profile, Ration, RationItem


def home(request):
    return render(request, 'nutrition/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile_detail')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'gender': 'female',
                    'age': 18,
                    'weight': 60,
                    'height': 170,
                    'activity_level': 'medium',
                    'goal': 'maintain',
                    'daily_budget': 300,
                }
            )

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Заполните профиль.')
            return redirect('profile_detail')
    else:
        form = RegisterForm()

    return render(request, 'nutrition/register.html', {'form': form})


@login_required
def profile_detail(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            'gender': 'female',
            'age': 18,
            'weight': 60,
            'height': 170,
            'activity_level': 'medium',
            'goal': 'maintain',
            'daily_budget': 300,
        }
    )

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно сохранён.')
            return redirect('profile_detail')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'user_obj': user,
        'profile': profile,
        'form': form,
    }
    return render(request, 'nutrition/profile.html', context)


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '')

    if selected_category:
        products = products.filter(category_id=selected_category)

    if search_query:
        products = [
            product for product in products
            if search_query.casefold() in product.name.casefold()
        ]

    if sort_by:
        if isinstance(products, list):
            if sort_by == 'calories':
                products = sorted(products, key=lambda x: x.calories_per_100g)
            elif sort_by == 'price':
                products = sorted(products, key=lambda x: x.price_per_100g)
            elif sort_by == 'proteins':
                products = sorted(
                    products,
                    key=lambda x: x.proteins_per_100g,
                    reverse=True
                )
        else:
            if sort_by == 'calories':
                products = products.order_by('calories_per_100g')
            elif sort_by == 'price':
                products = products.order_by('price_per_100g')
            elif sort_by == 'proteins':
                products = products.order_by('-proteins_per_100g')

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
        'sort_by': sort_by,
    }
    return render(request, 'nutrition/product_list.html', context)


@login_required
def ration_detail(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            'gender': 'female',
            'age': 18,
            'weight': 60,
            'height': 170,
            'activity_level': 'medium',
            'goal': 'maintain',
            'daily_budget': 300,
        }
    )

    selected_date = request.GET.get('date')
    available_rations = Ration.objects.filter(user=user).order_by('-date')

    if selected_date:
        ration = Ration.objects.filter(user=user, date=selected_date).first()
    else:
        ration = available_rations.first()

    if request.method == 'POST':
        if 'create_ration' in request.POST:
            ration_form = RationForm(request.POST)
            item_form = RationItemForm()

            if ration_form.is_valid():
                new_date = ration_form.cleaned_data['date']
                existing_ration = Ration.objects.filter(
                    user=user,
                    date=new_date
                ).first()

                if not existing_ration:
                    Ration.objects.create(user=user, date=new_date)
                    messages.success(request, 'Рацион успешно создан.')
                else:
                    messages.info(request, 'Рацион на эту дату уже существует.')

                return redirect(f'/ration/?date={new_date}')

        elif 'add_item' in request.POST:
            item_form = RationItemForm(request.POST)
            ration_form = RationForm()

            if item_form.is_valid() and ration:
                ration_item = item_form.save(commit=False)
                ration_item.ration = ration
                ration_item.save()
                messages.success(request, 'Продукт добавлен в рацион.')

                if selected_date:
                    return redirect(f'/ration/?date={selected_date}')
                return redirect('ration_detail')
    else:
        item_form = RationItemForm()
        ration_form = RationForm()

    context = {
        'user_obj': user,
        'profile': profile,
        'ration': ration,
        'form': item_form,
        'ration_form': ration_form,
        'available_rations': available_rations,
        'selected_date': selected_date,
    }
    return render(request, 'nutrition/ration_detail.html', context)


@login_required
def ration_analysis(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            'gender': 'female',
            'age': 18,
            'weight': 60,
            'height': 170,
            'activity_level': 'medium',
            'goal': 'maintain',
            'daily_budget': 300,
        }
    )

    selected_date = request.GET.get('date')
    available_rations = Ration.objects.filter(user=user).order_by('-date')

    if selected_date:
        ration = Ration.objects.filter(user=user, date=selected_date).first()
    else:
        ration = available_rations.first()

    context = {
        'user_obj': user,
        'profile': profile,
        'ration': ration,
        'available_rations': available_rations,
        'selected_date': selected_date,
    }
    return render(request, 'nutrition/ration_analysis.html', context)


@login_required
def dashboard(request):
    user = request.user
    rations = Ration.objects.filter(user=user).order_by('date')

    data = []
    for ration in rations:
        data.append({
            'date': ration.date,
            'calories': ration.total_calories(),
            'price': ration.total_price(),
            'proteins': ration.total_proteins(),
            'fats': ration.total_fats(),
            'carbs': ration.total_carbs(),
        })

    chart_html = None
    price_chart_html = None
    table_data = []

    if data:
        df = pd.DataFrame(data)
        table_data = df.to_dict(orient='records')

        fig_calories = px.line(
            df,
            x='date',
            y='calories',
            markers=True,
            title='Калорийность рациона по датам'
        )
        fig_calories.update_layout(
            xaxis_title='Дата',
            yaxis_title='Калории',
            template='plotly_white'
        )
        chart_html = fig_calories.to_html(full_html=False)

        fig_price = px.bar(
            df,
            x='date',
            y='price',
            title='Стоимость рациона по датам'
        )
        fig_price.update_layout(
            xaxis_title='Дата',
            yaxis_title='Стоимость',
            template='plotly_white'
        )
        price_chart_html = fig_price.to_html(full_html=False)

    context = {
        'user_obj': user,
        'chart_html': chart_html,
        'price_chart_html': price_chart_html,
        'table_data': table_data,
    }
    return render(request, 'nutrition/dashboard.html', context)


@login_required
def delete_ration_item(request, item_id):
    item = get_object_or_404(
        RationItem,
        id=item_id,
        ration__user=request.user
    )
    ration_date = item.ration.date

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Продукт удалён из рациона.')

    return redirect(f'/ration/?date={ration_date}')