from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.admin_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.user_list, name='user_list'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('categories/', views.category_list, name='category_list'),
    path('category/add/', views.category_add, name='category_add'),
    path('category/edit/<int:category_id>/', views.category_edit, name='category_edit'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('products/', views.product_list, name='product_list'),
    path('product/add/', views.product_add, name='product_add'),
    path('product/edit/<int:product_id>/', views.product_edit, name='product_edit'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]