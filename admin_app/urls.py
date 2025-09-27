from django.urls import path
from .views import index, user_list, toggle_user_status, category_list, category_add, category_edit, delete_category, product_list, product_add, product_edit, delete_product, admin_login, logout_view

app_name = 'admin'

urlpatterns = [
    path('', index, name='index'),
    path('login/', admin_login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('users/', user_list, name='user_list'),
    path('toggle-user-status/<int:user_id>/', toggle_user_status, name='toggle_user_status'),
    path('categories/', category_list, name='category_list'),
    path('category/add/', category_add, name='category_add'),
    path('category/edit/<int:category_id>/', category_edit, name='category_edit'),
    path('delete-category/<int:category_id>/', delete_category, name='delete_category'),
    path('products/', product_list, name='product_list'),
    path('product/add/', product_add, name='product_add'),
    path('product/edit/<int:product_id>/', product_edit, name='product_edit'),
    path('delete-product/<int:product_id>/', delete_product, name='delete_product'),
]