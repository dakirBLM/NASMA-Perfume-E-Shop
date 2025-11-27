from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_category_description_ar_category_description_cs_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(related_name='products', to='products.category'),
        ),
    ]
