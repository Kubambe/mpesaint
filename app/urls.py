# project-root/app/urls.py
"""app URL Configuration"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.custom_login, name='login'),
    path('signup/', views.custom_signup, name='signup'),
    path('logout/', views.custom_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    
    # Main Application URLs
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Product Management URLs
    path('product/create/', views.product_create, name='product_create'),
    path('product/update/<int:pk>/', views.product_update, name='product_update'),
    path('product/delete/<int:pk>/', views.product_delete, name='product_delete'),
    
    # Payment Processing URL
    path('pay/<int:product_id>/', views.initiate_payment, name='initiate_payment'),
    
    # M-Pesa Callback URL (for payment notifications)
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]