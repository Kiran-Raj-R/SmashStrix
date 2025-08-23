from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
         name = models.CharField(max_length=100, unique=True)
         created_at = models.DateTimeField(auto_now_add=True)

         def __str__(self):
             return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ProductSizeStock(models.Model):
    SIZE_CHOICES = [
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
    ]
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username}"  

class ProductSizeStock(models.Model):
    SIZE_CHOICES = [
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
    ]
    