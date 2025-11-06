from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order

@receiver(post_save, sender=Order)
def notify_admin_new_order(sender, instance, created, **kwargs):
    # Only trigger when a new order is created and status is pending
    if created and instance.status.lower() == 'pending':
        subject = f"🛍️ New Pending Order #{instance.order_number}"
        message = (
            f"A new order has been placed and is pending.\n\n"
            f"Order Number: {instance.order_number}\n"
            f"Customer: {instance.full_name}\n"
            f"Email: {instance.email}\n"
            f"Total Amount: {instance.final_total_formatted}\n"
            f"Created At: {instance.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Status: {instance.status}"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False
            )
        except Exception as e:
            print(f"Failed to send admin notification: {e}")
