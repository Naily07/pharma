from django.urls import path
from .views import *

urlpatterns = [
    path('', ListProduct.as_view(), name='produits'),
    path('create-product', CreateProduct.as_view(), name='create-produit'),
    path('create-stock', CreateBulkStock.as_view(), name='create-stock'),
    path('list/<str:expired>', ListProduct.as_view(), name='produit-expirer'),
    path('create-detail', CreateDetail.as_view(), name='create-detail'),
    path('delete-product/<int:pk>', DeleteProduct.as_view(), name='delete'),
    path('update-product/<int:pk>', UpdateProduct.as_view(), name='create-stock'),

    path('list-facture', ListFacture.as_view(), name='create-stock'),

    #Vendeur
    path('sell-product', SellBulkProduct.as_view(), name='vente-produit'),
    path('sell-one-product', SellProduct.as_view(), name='vente-produit'),
    path('sell-transaction', ListVente.as_view(), name='vente'),
    #Trosa
    path('list-trosa/', ListTrosa.as_view(), name='vente-produit'),
    path('create-trosa', CreateTrosa.as_view(), name='vente-produit'),
    path('delete-trosa/<int:pk>', DeleteTrosa.as_view(), name='vente-produit'),
    
]
