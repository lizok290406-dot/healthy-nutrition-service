from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('ration/<int:user_id>/', views.ration_detail, name='ration_detail'),
    path('analysis/<int:user_id>/', views.ration_analysis, name='ration_analysis'),
    path('dashboard/<int:user_id>/', views.dashboard, name='dashboard'),
    path('ration-item/delete/<int:item_id>/', views.delete_ration_item, name='delete_ration_item'),
]