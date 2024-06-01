from django.contrib import admin
from .models import *
# Register your models here.

class ModelProduct(admin.ModelAdmin):
    list_display = ['detail', 'qte_uniter', 'qte_gros']

class ModelVente(admin.ModelAdmin):
    list_display = ['pk', 'facture']

admin.site.register(Detail)
admin.site.register(Product, ModelProduct)
admin.site.register(Marque)
admin.site.register(VenteProduct, ModelVente)
admin.site.register(AjoutStock)
admin.site.register(Fournisseur)
admin.site.register(Facture)