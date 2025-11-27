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
    # Stripe integration fields
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    # Internal flag to ensure product stock is deducted exactly once
    stock_deducted = models.BooleanField(default=False)
    # Coupon/discount
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Capture previous status to detect transition to confirmed
        previous_status = None
        previous_stock_deducted = False
        if self.pk:
            old = Order.objects.filter(pk=self.pk).only('status', 'stock_deducted').first()
            if old:
                previous_status = old.status
                previous_stock_deducted = old.stock_deducted

        if not self.order_number:
            self.order_number = self.generate_order_number()

        # If status transitioned to confirmed via admin/manual change and stock not yet deducted
        if self.status == 'confirmed' and not self.stock_deducted:
            self.deduct_stock()

        super().save(*args, **kwargs)

    def generate_order_number(self):
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=6))
        return f'GF{date_part}{random_part}'

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"


    def send_status_email(self, old_status: str, old_tracking_number: str | None = None):
        """Send email notification when order status changes or tracking added."""
        subject = f"Order Update - #{self.order_number}"
        status_changed = (old_status != self.status)
        tracking_added = bool(self.tracking_number) and (old_tracking_number in (None, '',))
        context = {
            'order': self,
            'old_status': old_status,
            'new_status': self.status,
            'status_changed': status_changed,
            'tracking_added': tracking_added,
            'protocol': 'http' if settings.DEBUG else 'https',
            'domain': getattr(settings, 'SITE_DOMAIN', None) or (settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'),
        }
        html_message = render_to_string('orders/order_status_update.html', context)
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
            print(f"Failed to send customer status email: {e}")

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"

    def mark_as_paid(self, payment_intent_id: str, amount_minor_units: int):
        """Mark order as confirmed after successful Stripe payment.
        amount_minor_units: integer in minor currency unit (haléř) for CZK.
        Converts to stored whole CZK (dividing by 100) since model stores integers.
        Safe if called multiple times (idempotent)."""
        # Idempotency check
        if self.status == 'confirmed' and self.stripe_payment_intent == payment_intent_id:
            return
        previous_status = self.status
        self.status = 'confirmed'
        self.stripe_payment_intent = payment_intent_id
        if amount_minor_units is not None:
            self.paid_amount = amount_minor_units // 100
        # Deduct stock once when payment confirms
        if not self.stock_deducted:
            self.deduct_stock()
        # Set admin notification flag proactively (in case pre_save not executed in some contexts)
        self._notify_admin_confirmed = (previous_status != 'confirmed')
        self.save()

    # --- Internal helper methods ---
    def deduct_stock(self):
        """Deduct product stock quantities for this order's items once.
        Safe against multiple calls (checks stock_deducted flag)."""
        if self.stock_deducted:
            return
        for item in self.items.select_related('product').all():
            product = item.product
            new_qty = product.stock_quantity - item.quantity
            if new_qty < 0:
                new_qty = 0
            product.stock_quantity = new_qty
            product.save(update_fields=['stock_quantity'])
        self.stock_deducted = True


    @property
    def final_total(self):
        total = self.total_amount + self.shipping_cost + self.tax_amount
        if self.discount_amount:
            total = max(0, total - int(self.discount_amount))
        return total

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


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=0, help_text="Discount amount in CZK (whole koruna)")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} (-{self.amount} CZK)"

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

