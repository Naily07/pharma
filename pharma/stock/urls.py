from django.urls import path
from .views import *

urlpatterns = [
    path('list-product', ListProduct.as_view(), name='produits'),
    path('create-product', CreateProduct.as_view(), name='create-produit'),
    path('create-detail', CreateDetail.as_view(), name='create-produit'),
    path('update-product', UpdateProduct.as_view(), name='create-produit'),
    path('create-stock', CreateBulkStock.as_view(), name='create-stock'),

    #Vendeur
    path('update-product', SellProduct.as_view(), name='vente-produit'),
]
