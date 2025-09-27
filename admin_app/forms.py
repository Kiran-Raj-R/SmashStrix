from django import forms
from user_app.models import Product
from django.utils import timezone

class AdminLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_products = Product.objects.filter(is_deleted=False)

        selected_products = self.instance.products.all() if self.instance.pk else Product.objects.none()
        unselected_products = all_products.exclude(pk__in=selected_products)

        self.selected_products = selected_products
        self.unselected_products = unselected_products

        self.fields['products'].queryset = all_products
        self.fields['products'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        products = cleaned_data.get('products')

        if start and end and start >= end:
            self.add_error('start_date', "Start date must be before end date.")
        if not products or len(products) == 0:
            self.add_error('products', "Please select at least one product.")

        return cleaned_data

