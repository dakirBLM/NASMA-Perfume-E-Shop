from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0006_remove_order_payment_method_order_paid_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stock_deducted',
            field=models.BooleanField(default=False),
        ),
    ]
