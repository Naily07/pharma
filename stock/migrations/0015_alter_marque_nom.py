# Generated by Django 5.0.6 on 2024-07-13 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0014_trosa_adress_trosa_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marque',
            name='nom',
            field=models.CharField(max_length=50),
        ),
    ]