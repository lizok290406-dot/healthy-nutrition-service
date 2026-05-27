from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),

    path('register/', views.register_view, name='register'),

    path('profile/', views.profile_detail, name='profile_detail'),
    path('ration/', views.ration_detail, name='ration_detail'),
    path('analysis/', views.ration_analysis, name='ration_analysis'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('ration-item/delete/<int:item_id>/', views.delete_ration_item, name='delete_ration_item'),
]