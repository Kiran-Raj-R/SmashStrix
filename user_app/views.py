from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import random
from .models import OTP, Product, User
import logging
from django.conf import settings
from social_django.utils import psa
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'user_app/index.html')

@login_required
def user_page(request):
    logger.info(f"User page accessed by user: {request.user.email}")
    return render(request, 'user_app/user_page.html')

@csrf_protect
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        logger.info(f"Login attempt for email: {email}")
        if not all([email, password]):
            logger.warning("Login failed: Missing email or password")
            return render(request, 'user_app/login.html', {'error': 'All fields are required'})
        user = authenticate(request, username=email, password=password)
        if user:
            logger.info(f"User {email} authenticated successfully")
            if user.is_active and not user.is_superuser:
                login(request, user)
                logger.info(f"User {email} logged in, setting success flag")
                request.session['login_success'] = True
                request.session.modified = True
                return redirect('home')
            elif not user.is_active:
                return render(request, 'user_app/login.html', {'error': 'Your account is blocked. Please contact the administrator'})
            else:
                logger.warning(f"Login denied for {email}: Inactive or admin user")
                return render(request, 'user_app/login.html', {'error': 'Account inactive or admin access denied'})
        else:
            logger.error(f"Authentication failed for {email}")
            return render(request, 'user_app/login.html', {'error': 'Invalid email or password'})
    return render(request, 'user_app/login.html')

@psa('social:complete')
def social_signup_complete(request, backend):
    user = request.backend.do_auth(request)
    if user and not user.is_superuser:
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'user_app/login.html', {'error': 'Social authentication failed or admin access denied'})

def signup_form(request):
    if request.method == 'POST':
        fullname = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        mobile_number = request.POST['mobile_number']
        username = fullname.replace(' ', '_')
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        if User.objects.filter(email=email).exists() or User.objects.filter(mobile_num=mobile_number).exists():
            return render(request, 'user_app/signup.html', {'error': 'Email or mobile number already exists'})
        if not all([fullname, email, password, confirm_password, mobile_number]):
            return render(request, 'user_app/signup.html', {'error': 'All fields are required'})
        if password != confirm_password:
            return render(request, 'user_app/signup.html', {'error': 'Passwords do not match'})
        if len(password) < 6:
            return render(request, 'user_app/signup.html', {'error': 'Password must be at least 6 characters'})
        user = User.objects.create_user(username=username, email=email, password=password, is_active=False, fullname=fullname, mobile_num=mobile_number)
        code = ''.join(random.choices('0123456789', k=6))
        OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
        try:
            send_mail(
                'Your OTP for SmashStrix Signup',
                f'Your OTP is {code}. It expires in 5 minutes. Please enter it to verify your account.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent to {email} with code: {code}")
            request.session['user_id'] = user.id
            request.session['otp_expiry'] = (timezone.now() + timezone.timedelta(minutes=5)).isoformat()
            return redirect('verify_otp')
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            user.delete()
            return render(request, 'user_app/signup.html', {'error': 'Failed to send OTP. Please try again later.'})
    return render(request, 'user_app/signup.html', {'current_time': timezone.now().isoformat()})

def verify_otp(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('signup')
        code = request.POST['otp']
        try:
            otp = OTP.objects.get(user_id=user_id, code=code, expires_at__gt=timezone.now())
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            otp.delete()
            request.session['signup_success'] = True
            request.session.modified = True 
            del request.session['signup_success']
            request.session.modified = True
            return render(request, 'user_app/signup.html', {
                'show_alert': True,
                'current_time': timezone.now().isoformat()
            })
        except OTP.DoesNotExist:
            return render(request, 'user_app/signup.html', {'error': 'Invalid or expired OTP', 'show_otp': True})
    return render(request, 'user_app/signup.html', {'show_otp': True, 'current_time': timezone.now().isoformat()})

@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        data = request.POST
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            code = ''.join(random.choices('0123456789', k=6))
            OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
            try:
                send_mail(
                    'Your OTP Code',
                    f'Your OTP is {code}. It expires in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                logger.info(f"Resend OTP email sent to {user.email} with code: {code}")
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Failed to resend OTP email to {user.email}: {str(e)}")
                return JsonResponse({'success': False})
        except User.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

@csrf_protect
def clear_signup_success(request):
    if request.method == 'POST':
        if 'signup_success' in request.session:
            del request.session['signup_success']
            request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@csrf_protect
def clear_login_success(request):
    if request.method == 'POST':
        if 'login_success' in request.session:
            del request.session['login_success']
            request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            if user.is_superuser:
                return render(request, 'user_app/login.html', {'error': 'Admin password reset not supported via this method', 'show_forgot': True})
            code = ''.join(random.choices('0123456789', k=6))
            OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
            try:
                send_mail(
                    'Password Reset OTP',
                    f'Your OTP is {code}. It expires in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                logger.info(f"OTP email sent to {email} with code: {code}")
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
                if user.is_superuser:
                    return render(request, 'user_app/login.html', {'error': 'Admin password reset not supported via this method', 'show_reset': True})
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

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.stock_count > 0:
        return redirect('product_detail', product_id=product_id)
    return render(request, 'product_detail.html', {'product': product, 'error': 'Out of stock'})