from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from user_app.models import Category, Product, ProductImage
from django.http import JsonResponse
from PIL import Image
import os
from django.conf import settings
from django.contrib.auth import authenticate, login, logout

def is_admin(user):
    return user.is_superuser

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin:index')
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid credentials or insufficient permissions'})
    return render(request, 'admin_login.html')

@staff_member_required
def logout_view(request):
    logout(request)
    return redirect('admin:login')

@staff_member_required
def index(request):
    user_count = User.objects.count()
    category_count = Category.objects.count()
    product_count = Product.objects.filter(is_active=True).count()
    return render(request, 'admin_dashboard.html', {
        'user_count': user_count,
        'category_count': category_count,
        'product_count': product_count,
    })

@staff_member_required
def user_list(request):
    search_query = request.GET.get('search', '')
    users = User.objects.all()
    if search_query:
        users = users.filter(fullname__icontains=search_query) | users.filter(email__icontains=search_query)
    users = users.order_by('-date_joined')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'user_management.html', {'users': page_obj})

@staff_member_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_blocked = not user.is_blocked
    user.save()
    return JsonResponse({'status': 'success', 'is_blocked': user.is_blocked})

@staff_member_required
def category_list(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.all()
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    categories = categories.order_by('-created_at')
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'category_management.html', {'categories': page_obj})

@staff_member_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description', '')
        category_img = request.FILES.get('category_img') if 'category_img' in request.FILES else None
        category = Category.objects.create(name=name, description=description, category_img=category_img)
        return redirect('admin:category_list')
    return render(request, 'add_category.html')

@staff_member_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if request.method == 'POST':
        category.name = request.POST['name']
        category.description = request.POST.get('description', '')
        if 'category_img' in request.FILES:
            category.category_img = request.FILES['category_img']
        category.save()
        return redirect('admin:category_list')
    return render(request, 'edit_category.html', {'category': category})

@staff_member_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    category.delete() 
    return JsonResponse({'status': 'success'})

@staff_member_required
def product_list(request):
    search_query = request.GET.get('search', '')
    products = Product.objects.filter(is_active=True)
    if search_query:
        products = products.filter(name__icontains=search_query)
    products = products.order_by('-created_at')
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'product_management.html', {'products': page_obj})

@staff_member_required
def product_add(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description', '')
        category_id = request.POST['category_id']
        category = get_object_or_404(Category, pk=category_id)
        price = request.POST.get('price', 0.00)
        stock_count = request.POST.get('stock_count', 0)
        rating = request.POST.get('rating', 0.0)
        product = Product.objects.create(name=name, description=description, category=category, price=price, stock_count=stock_count, rating=rating)
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            if len(images) < 3:
                product.delete()
                return render(request, 'add_product.html', {'categories': Category.objects.all(), 'error': 'Minimum 3 images required'})
            for img in images:
                img_instance = Image.open(img)
                img_instance = img_instance.resize((300, 300), Image.Resampling.LANCZOS)
                img_path = os.path.join(settings.MEDIA_ROOT, f'products/{img.name}')
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img_instance.save(img_path)
                ProductImage.objects.create(product=product, img_url=img)
        return redirect('admin:product_list')
    return render(request, 'add_product.html', {'categories': Category.objects.all()})

@staff_member_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST.get('description', '')
        category_id = request.POST['category_id']
        product.category = get_object_or_404(Category, pk=category_id)
        product.price = request.POST.get('price', product.price)
        product.stock_count = request.POST.get('stock_count', 0)
        product.rating = request.POST.get('rating', 0.0)
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            if len(images) < 3 and not product.images.exists():
                return render(request, 'edit_product.html', {'categories': Category.objects.all(), 'product': product, 'error': 'Minimum 3 images required'})
            ProductImage.objects.filter(product=product).delete()
            for img in images:
                img_instance = Image.open(img)
                img_instance = img_instance.resize((300, 300), Image.Resampling.LANCZOS)
                img_path = os.path.join(settings.MEDIA_ROOT, f'products/{img.name}')
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img_instance.save(img_path)
                ProductImage.objects.create(product=product, img_url=img)
        product.save()
        return redirect('admin:product_list')
    return render(request, 'edit_product.html', {'categories': Category.objects.all(), 'product': product})


@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.is_active = False
    product.save()
    return JsonResponse({'status': 'success'})