from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/products/', views.product_list, name='product_list'),
    path('api/categories/', views.category_list, name='category_list'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_form, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
]