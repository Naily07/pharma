from django.urls import path
from .views import *

urlpatterns = [
    path('', ListProduct.as_view(), name='produits'),
    path('create-product', CreateProduct.as_view(), name='create-produit'),
    path('create-detail', CreateDetail.as_view(), name='create-detail'),
    path('update-product', UpdateProduct.as_view(), name='create-produit'),
    path('delete-product/<int:pk>', DeleteProduct.as_view(), name='delete'),
    path('update-product/<int:pk>', UpdateProduct.as_view(), name='create-stock'),

    path('create-stock', CreateBulkStock.as_view(), name='create-stock'),

    path('list-facture', ListFacture.as_view(), name='create-stock'),

    #Vendeur
    path('sell-product', SellBulkProduct.as_view(), name='vente-produit'),
    path('sell-one-product', SellProduct.as_view(), name='vente-produit'),
]
