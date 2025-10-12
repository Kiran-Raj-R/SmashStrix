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
    path('toggle-category-status/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('brands/', views.brand_management, name='brand_management'),
    path('brands/add/', views.add_brand, name='add_brand'),
    path('brands/edit/<int:brand_id>/', views.edit_brand, name='edit_brand'),
    path('toggle-brand-status/<int:brand_id>/', views.toggle_brand_status, name='toggle_brand_status'),
    path('delete-brand/<int:brand_id>/', views.delete_brand, name='delete_brand'),
    path('products/', views.product_list, name='product_list'),
    path('product/add/', views.product_add, name='product_add'),
    path('product/edit/<int:product_id>/', views.product_edit, name='product_edit'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]