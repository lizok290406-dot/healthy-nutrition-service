from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('catalog/', views.food_catalog, name='food_catalog'),
    path('food/add/', views.add_food_item, name='add_food_item'),
    path('food/<int:pk>/', views.food_detail, name='food_detail'),
    path('meal/add/', views.add_meal, name='add_meal'),
    path('meal/delete/<int:pk>/', views.delete_meal, name='delete_meal'),
    path('weight/log/', views.log_weight, name='log_weight'),
    path('progress/', views.progress, name='progress'),
    path('calculator/', views.calorie_calculator, name='calorie_calculator'),
    path('api/search-food/', views.search_food_api, name='search_food_api'),
]