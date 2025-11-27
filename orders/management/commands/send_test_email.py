from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email to ADMIN_EMAIL to verify SMTP configuration."

    def handle(self, *args, **options):
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if not admin_email:
            self.stderr.write(self.style.ERROR('ADMIN_EMAIL is not configured.'))
            return
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')
        subject = 'Test email from NASMA Perfume E-Shop'
        message = 'This is a test email to confirm SMTP settings are working.'
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Sent test email to {admin_email} from {from_email}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to send test email: {e}'))
