from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.food_catalog, name='food_catalog'),
    path('recommend/', views.recommend, name='recommend'),
    path('analysis/', views.analysis, name='analysis'),
    path('food/<int:pk>/', views.food_detail, name='food_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-meal/', views.add_meal, name='add_meal'),
    path('add-food/', views.add_food_item, name='add_food_item'),
    path('delete-meal/<int:pk>/', views.delete_meal, name='delete_meal'),
    path('budget/', views.budget_view, name='budget'),
    path('progress/', views.progress, name='progress'),
    path('calculator/', views.calorie_calculator, name='calorie_calculator'),
    path('log-weight/', views.log_weight, name='log_weight'),
    path('api/search-food/', views.api_search_food, name='api_search_food'),
]