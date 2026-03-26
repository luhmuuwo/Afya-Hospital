# Generated migration for MPesaTransaction model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_rename_medicine_pharmacyitem_pharmacyissue_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MPesaTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_phone', models.CharField(max_length=15)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_id', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')], default='Pending', max_length=20)),
                ('mpesa_receipt', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('response_data', models.TextField(blank=True, help_text='Raw M-Pesa response data', null=True)),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_transactions', to='myapp.bill')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
