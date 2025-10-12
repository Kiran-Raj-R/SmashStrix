from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    fullname = models.CharField(max_length=255, null=False)
    mobile_num = models.CharField(max_length=15, null=False)
    email = models.EmailField(unique=True)
    referral_code = models.CharField(max_length=50, null=True)
    is_admin = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.fullname

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='brand_icons/')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    stock_count = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    img_url = models.ImageField(upload_to='products/', null=True, blank=True)
    alt_text = models.CharField(max_length=255, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return f"Image for {self.product.name}"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.code}"
    