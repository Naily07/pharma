# Generated by Django 5.0.6 on 2024-06-07 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0007_alter_fournisseur_nom'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ajoutstock',
            name='facture',
        ),
        migrations.AlterField(
            model_name='facture',
            name='client',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
