from django.urls import path, include
from . import views
from social_django.urls import urlpatterns as social_urlpatterns


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.signup_form, name='signup'),
    path('user/', views.user_page, name='user_page'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('clear-signup-success/', views.clear_signup_success, name='clear_signup_success'),
    path('clear-login-success/', views.clear_login_success, name='clear_login_success'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
    path('complete/<backend>/', views.social_signup_complete, name='complete'),
    path('', include((social_urlpatterns))), 
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('shop/',views.shop,name='shop'),
]