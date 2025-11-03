# orders/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

class Order(models.Model):
   

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=100, null=True, blank=True )
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
       # Change to CZK - Czech Koruna typically doesn't use decimal places
    total_amount = models.DecimalField(max_digits=10, decimal_places=0)  # Whole CZK
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=0, default=250)  # 250 CZK default
    tax_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    tracking_company = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=6))
        return f'GF{date_part}{random_part}'

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"
    
    
    def send_status_email(self, old_status):
        """Send email notification when order status changes"""
        subject = f"Order Update - #{self.order_number}"
        
        context = {
            'order': self,
            'old_status': old_status,
            'new_status': self.status,
            'status_changed': old_status != self.status,
            'tracking_added': self.tracking_number and not Order.objects.get(pk=self.pk).tracking_number,
        }
        
        html_message = render_to_string('orders/email/order_status_update.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't break the save process
            print(f"Failed to send email: {e}")

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"


    @property
    def final_total(self):
        return self.total_amount + self.shipping_cost + self.tax_amount
    
    @property
    def final_total_formatted(self):
        return f"{self.final_total} Kč"
    
    @property
    def total_amount_formatted(self):
        return f"{self.total_amount} Kč"
    
    @property
    def shipping_cost_formatted(self):
        return f"{self.shipping_cost} Kč"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0)  

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.price

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"