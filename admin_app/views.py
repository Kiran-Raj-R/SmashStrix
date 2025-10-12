from user_app.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from user_app.models import Category, Product, ProductImage, Brand
from django.http import JsonResponse
from PIL import Image
import os
import logging
from django.db.models import Q
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, login, logout

logger = logging.getLogger(__name__)

def admin_login(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('admin:index')
            else:
                messages.error(request, 'Insufficient permissions. Only staff or superuser can log in.')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'admin_login.html')


@staff_member_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('admin:login')

@staff_member_required
def index(request):
    user_count = User.objects.filter(is_superuser = False).count()
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
    users = User.objects.filter(is_superuser = False)
    if search_query:
        users = users.filter(Q(username__icontains=search_query)) | users.filter(Q(email__icontains=search_query))
    users = users.order_by('-date_joined')
    paginator = Paginator(users, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'user_management.html', {'page_obj': page_obj})

@staff_member_required
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        old_status = user.is_active
        user.is_active = not user.is_active
        user.save()
        new_status = user.is_active
        logger.info(f'User {user_id} status changed from {old_status} to {new_status}')
        user.refresh_from_db()
        if old_status == new_status:
            logger.error(f"Save failed for user {user_id}: No change detected")
        return JsonResponse({'status': 'success', 'is_active': user.is_active})
    return JsonResponse({'status':'error','message':'Invalid request method'},status=400)


@staff_member_required
def category_list(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.filter(name__icontains=search_query, is_deleted=False).order_by('name')
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'category_management.html', {'page_obj': page_obj})

@staff_member_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_deleted = request.POST.get('is_deleted') == 'on'

        category = Category(
            name=name,
            description=description,
            is_active=is_active,
            is_deleted=is_deleted
        )
        category.save()
        messages.success(request, f"Category '{name}' added successfully.")
        return redirect('admin:category_list')

    return render(request, 'add_category.html')


@staff_member_required
@csrf_exempt
def toggle_category_status(request, category_id):
    print(f"Toggle called for category_id: {category_id}")
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=category_id, is_deleted=False)
        category.is_active = not category.is_active
        category.save()
        print(f"Category {category.name} is_active set to: {category.is_active}")
        return JsonResponse({'status': 'success', 'is_active': category.is_active})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@staff_member_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id, is_deleted=False)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        is_deleted = request.POST.get('is_deleted') == 'on'

        category.name = name
        category.description = description
        category.is_active = is_active
        category.is_deleted = is_deleted
        category.save()
        messages.success(request, f"Category '{name}' updated successfully.")
        return redirect('admin:category_list')

    return render(request, 'edit_category.html', {'category': category})

@staff_member_required
@csrf_exempt
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=category_id, is_deleted=False)
        category.is_deleted = True
        category.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@staff_member_required
def brand_management(request):
    search_query = request.GET.get('search', '')
    brands = Brand.objects.filter(name__icontains=search_query, is_deleted=False).order_by('name')
    paginator = Paginator(brands, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'brand_management.html', {'page_obj': page_obj})

@staff_member_required
def add_brand(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.FILES.get('icon')
        is_active = request.POST.get('is_active') == 'on'
        is_deleted = request.POST.get('is_deleted') == 'on'

        brand = Brand(
            name=name,
            icon=icon,
            is_active=is_active,
            is_deleted=is_deleted
        )
        brand.save()
        messages.success(request, f"Brand '{name}' added successfully.")
        return redirect('admin:brand_management')

    return render(request, 'add_brand.html')

@staff_member_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id, is_deleted=False)
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.FILES.get('icon')
        is_active = request.POST.get('is_active') == 'on'
        is_deleted = request.POST.get('is_deleted') == 'on'

        brand.name = name
        if icon:
            brand.icon = icon
        brand.is_active = is_active
        brand.is_deleted = is_deleted
        brand.save()
        messages.success(request, f"Brand '{name}' updated successfully.")
        return redirect('admin:brand_management')

    return render(request, 'edit_brand.html', {'brand': brand})

@staff_member_required
@csrf_exempt
def toggle_brand_status(request, brand_id):
    if request.method == 'POST':
        brand = get_object_or_404(Brand, pk=brand_id, is_deleted=False)
        brand.is_active = not brand.is_active
        brand.save()
        return JsonResponse({'status': 'success', 'is_active': brand.is_active})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@staff_member_required
@csrf_exempt
def delete_brand(request, brand_id):
    if request.method == 'POST':
        brand = get_object_or_404(Brand, pk=brand_id, is_deleted=False)
        brand.is_deleted = True
        brand.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

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