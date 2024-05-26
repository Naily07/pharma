from django.contrib import admin
from .models import *
# Register your models here.

class ModelProduct(admin.ModelAdmin):
    list_display = ['detail', 'qte_uniter', 'qte_gros']

admin.site.register(Detail)
admin.site.register(Product, ModelProduct)