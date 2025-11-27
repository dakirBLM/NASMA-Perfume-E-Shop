<<<<<<< HEAD
from django.db.models.signals import post_save, pre_save
=======
from django.db.models.signals import post_save
>>>>>>> 262ce5adbee25db4f7d2a12bc1b12711e3671eb8
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
<<<<<<< HEAD
            f"A new order has been placed.\n\n"
            f"Order ID: {instance.id}\n"
=======
            f"A new order has been placed and is pending.\n\n"
>>>>>>> 262ce5adbee25db4f7d2a12bc1b12711e3671eb8
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
<<<<<<< HEAD


@receiver(post_save, sender=Order)
def notify_admin_order_confirmed(sender, instance, created, **kwargs):
    """Notify admin when an order transitions to confirmed (flag set in pre_save)."""
    if created:
        return
    if getattr(instance, '_notify_admin_confirmed', False):
        subject = f"✅ Order Confirmed #{instance.order_number}"
        message = (
            f"An order has been confirmed and paid.\n\n"
            f"Order ID: {instance.id}\n"
            f"Order Number: {instance.order_number}\n"
            f"Customer: {instance.full_name}\n"
            f"Email: {instance.email}\n"
            f"Paid Amount: {instance.paid_amount or instance.final_total} Kč\n"
            f"Status: {instance.status}"
        )
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or 'dakirblm@gmail.com'
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False
            )
        except Exception as e:
            print(f"Failed to send admin confirmed notification: {e}")


@receiver(pre_save, sender=Order)
def notify_customer_status_change(sender, instance, **kwargs):
    """Send an email to the customer if status changes or tracking added."""
    if not instance.pk:
        return
    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return
    status_changed = old.status != instance.status
    tracking_added = (not old.tracking_number) and bool(instance.tracking_number)
    # Flag for admin notification after save
    instance._notify_admin_confirmed = (old.status != 'confirmed' and instance.status.lower() == 'confirmed')
    if status_changed or tracking_added:
        try:
            instance.send_status_email(old_status=old.status, old_tracking_number=old.tracking_number)
        except Exception as e:
            print(f"Failed to send customer status change email: {e}")
=======
>>>>>>> 262ce5adbee25db4f7d2a12bc1b12711e3671eb8
