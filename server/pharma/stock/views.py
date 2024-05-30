from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from .models import *
from .serialiser import *
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class ListProduct(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser

class CreateProduct(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser

class CreateBulkStock(APIView):
    
    def post(self, request):
        productsToCreate = []
        productsToUpdate = []
        productList = request.data
        try:
            for newProduct in productList:
                detail = newProduct.pop('detail')
                marque = newProduct.pop('marque')
                fournisseur = newProduct.pop('fournisseur')
                detailInstance, created = Detail.objects.get_or_create(
                    designation=detail['designation'], 
                    famille=detail['famille'], 
                    classe=detail['classe'], 
                    type_uniter=detail['type_uniter'], 
                    type_gros=detail['type_gros'],
                    qte_max = detail['qte_max']
                )

                marqueInstance, created = Marque.objects.get_or_create(nom = marque)
                fournisseurInstance, created = Fournisseur.objects.get_or_create(nom = fournisseur)
                productExist = Product.objects.filter(
                    detail = detailInstance, marque = marqueInstance, fournisseur = fournisseurInstance
                    ).first()
                
                print("gros", newProduct['qte_gros'])
                if productExist:
                    productExist.qte_gros += newProduct['qte_gros']
                #Test de quantiter maximum d'uniter
                while newProduct['qte_uniter'] >= detailInstance.qte_max: 
                    productExist.qte_gros += 1
                    newProduct['qte_uniter'] -= detailInstance.qte_max

                if productExist:
                    productExist.qte_uniter = newProduct['qte_uniter']
                    productsToUpdate.append(productExist)
                else:
                    productsToCreate.append(Product(**newProduct, detail = detailInstance)) 

                print(f"this {detail} is created {created}")
                print(productsToCreate)
            
            if len(productsToUpdate)>0:
                Product.objects.bulk_update(productsToUpdate, fields=['prix_uniter', 'prix_gros', 'qte_uniter', 'qte_gros'])
            if len(productsToCreate)>0:
                Product.objects.bulk_create(productsToCreate)
            return Response(f"Success", status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(f'Error {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProduct(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser

class SellProduct(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    
class CreateDetail(generics.ListCreateAPIView): 
    queryset = Detail.objects.all()
    serializer_class = DetailSerialiser

