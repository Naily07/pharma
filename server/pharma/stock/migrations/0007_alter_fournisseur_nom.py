# Generated by Django 5.0.6 on 2024-06-02 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0006_facture_client_alter_ajoutstock_gestionnaire'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fournisseur',
            name='nom',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
