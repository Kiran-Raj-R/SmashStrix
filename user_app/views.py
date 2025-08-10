from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Product, Category, Profile, OTP, User
from .serializers import ProductSerializer, CategorySerializer
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
import random
import string
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from social_django.utils import psa
import logging
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

class ProductPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'

@api_view(['GET'])
def product_list(request):
    products = Product.objects.filter(is_active=True, stock__gt=0)
    search = request.GET.get('search', '')
    if search:
        products = products.filter(Q(name__icontains=search) | Q(category__name__icontains=search))
    sort = request.GET.get('sort', '')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category__id=category)
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)
    paginator = ProductPagination()
    paginated_products = paginator.paginate_queryset(products, request)
    serializer = ProductSerializer(paginated_products, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk, is_active=True, stock__gt=0)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return redirect('home')

def home(request):
    return render(request, 'user_app/index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if not all([username, password]):
            return render(request, 'user_app/login.html', {'error': 'All fields are required'})
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        return render(request, 'user_app/login.html', {'error': 'Invalid credentials'})
    return render(request, 'user_app/login.html')

def signup_form(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            return render(request, 'user_app/signup.html', {'error': 'Username already exists'})
        if not all([username, email, password]):
            return render(request, 'user_app/signup.html', {'error': 'All fields are required'})
        if len(password) < 6:
            return render(request, 'user_app/signup.html', {'error': 'Password must be at least 6 characters'})
        user = User.objects.create_user(username=username, email=email, password=password)
        code = ''.join(random.choices(string.digits, k=6))
        OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
        try:
            send_mail(
                'Your OTP Code',
                f'Your OTP is {code}. It expires in 5 minutes.',
                settings.DEFAULT_FROM_EMAIL,  # Use settings module to access it
                [email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent to {email}")
            request.session['user_id'] = user.id
            return redirect('verify_otp')
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return render(request, 'user_app/signup.html', {'error': 'Failed to send OTP. Check your email settings.'})
    return render(request, 'user_app/signup.html')

@psa('social:complete')
def social_signup_complete(request, backend):
    user = request.backend.do_auth(request)
    if user:
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'user_app/signup.html', {'error': 'Social authentication failed'})

def verify_otp(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('signup')
        code = request.POST['otp']
        try:
            otp = OTP.objects.get(user_id=user_id, code=code, expires_at__gt=timezone.now())
            otp.delete()
            user = User.objects.get(id=user_id)
            login(request, user)
            del request.session['user_id']
            return redirect('home')
        except OTP.DoesNotExist:
            return render(request, 'user_app/signup.html', {'error': 'Invalid or expired OTP', 'show_otp': True})
    return render(request, 'user_app/signup.html', {'show_otp': True})

@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        data = request.POST
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            code = ''.join(random.choices(string.digits, k=6))
            OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
            try:
                send_mail(
                    'Your OTP Code',
                    f'Your OTP is {code}. It expires in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                logger.info(f"Resend OTP email sent to {user.email}")
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Failed to resend OTP email to {user.email}: {str(e)}")
                return JsonResponse({'success': False})
        except User.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            code = ''.join(random.choices(string.digits, k=6))
            OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
            try:
                send_mail(
                    'Password Reset OTP',
                    f'Your OTP is {code}. It expires in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                logger.info(f"Forgot password OTP sent to {email}")
                request.session['reset_user_id'] = user.id
                return redirect('reset_password')
            except Exception as e:
                logger.error(f"Failed to send forgot password OTP to {email}: {str(e)}")
                return render(request, 'user_app/login.html', {'error': 'Failed to send OTP. Check your email settings.', 'show_forgot': True})
        except User.DoesNotExist:
            return render(request, 'user_app/login.html', {'error': 'Email not found', 'show_forgot': True})
    return render(request, 'user_app/login.html', {'show_forgot': True})

def reset_password(request):
    if request.method == 'POST':
        user_id = request.session.get('reset_user_id')
        if not user_id:
            return redirect('login')
        code = request.POST['otp']
        try:
            otp = OTP.objects.get(user_id=user_id, code=code, expires_at__gt=timezone.now())
            otp.delete()
            if 'new_password' in request.POST:
                new_password = request.POST['new_password']
                if len(new_password) < 6:
                    return render(request, 'user_app/login.html', {'error': 'Password must be at least 6 characters', 'show_reset': True})
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                del request.session['reset_user_id']
                return redirect('login')
            return render(request, 'user_app/login.html', {'show_reset': True})
        except OTP.DoesNotExist:
            return render(request, 'user_app/login.html', {'error': 'Invalid or expired OTP', 'show_reset': True})
    return render(request, 'user_app/login.html', {'show_reset': True})

def logout_view(request):
    logout(request)
    return redirect('home')