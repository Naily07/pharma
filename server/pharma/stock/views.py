from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from .models import *
from .serialiser import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

# Create your views here.

class CreateDetail(generics.ListCreateAPIView): 
    queryset = Detail.objects.all()
    serializer_class = DetailSerialiser
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
                detailInstance, createdD = Detail.objects.get_or_create(
                    designation=detail['designation'], 
                    famille=detail['famille'], 
                    classe=detail['classe'], 
                    type_uniter=detail['type_uniter'], 
                    type_gros=detail['type_gros'],
                    qte_max = detail['qte_max']
                )

                marqueInstance, createdM = Marque.objects.get_or_create(nom = marque)
                fournisseurInstance, createdF = Fournisseur.objects.get_or_create(
                    nom = fournisseur['nom'],
                    adress = fournisseur['adress'],
                    contact = fournisseur['contact']
                )
                productExist = Product.objects.filter(
                    detail = detailInstance, marque = marqueInstance, fournisseur = fournisseurInstance
                    ).first()
                
                print("gros", newProduct['qte_gros'])
                print("Exist", productExist)
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
                    productsToCreate.append(Product(**newProduct, detail = detailInstance, fournisseur = fournisseurInstance, marque = marqueInstance)) 

                print(f"this {detail} is created {createdD}")
                print(productsToCreate)
            
            if len(productsToUpdate)>0:
                Product.objects.bulk_update(productsToUpdate, fields=['prix_uniter', 'prix_gros', 'qte_uniter', 'qte_gros'])
            if len(productsToCreate)>0:
                Product.objects.bulk_create(productsToCreate)
            return Response(f"Success", status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(f'Error {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProduct(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    lookup_field = 'pk'

    def patch(self, request, *args, **kwargs):
        #Traitement de qte_max
        return super().patch(request, *args, **kwargs)
    

class DeleteProduct(generics.DestroyAPIView, generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser


class SellProduct(generics.ListCreateAPIView):
    queryset = VenteProduct.objects.all()
    serializer_class = VenteProductSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            prix_uniter = 0
            prix_gros = 0
            produit = Product.objects.filter(id=serializer.validated_data.get('product_id')).first()
            maxUniter = produit.detail.qte_max
            qte_uniter = serializer.validated_data.get('qte_uniter_transaction')
            qte_gros = serializer.validated_data.get('qte_gros_transaction')
            if qte_uniter > maxUniter or qte_gros > produit.qte_gros or qte_uniter > produit.qte_uniter :
                raise ValidationError(detail={"message" : 'la quantité est invalide'})
            if qte_uniter > 0 :
                produit.qte_uniter -= qte_uniter
                prix_uniter = qte_uniter * produit.prix_uniter
            if qte_gros > 0 :
                produit.qte_gros -= qte_gros
                prix_gros = qte_gros * produit.qte_gros
            produit.save()
            facture = Facture.objects.create(
                prix_total = prix_gros + prix_uniter,
                prix_restant = 0
            )

            serializer.save(facture = facture)
            instanceP = serializer.instance
        #Capture l'erreur de validation
        except ValidationError as e:
            raise e
        except Exception as e:
            raise BaseException()


class SellBulkProduct(APIView):
    
    #Transaction des Ventes en Masses
    def post(self, request):
        venteList = request.data
        venteInstancList = []
        try:
            facture = Facture(
                prix_total = 0,
                prix_restant = 0
            )
            prix_uniter = 0
            prix_gros = 0
            for vente in venteList:
                product_id = vente['product_id']
                produit = Product.objects.filter(id=product_id).first()
                maxUniter = produit.detail.qte_max
                qte_uniter = vente['qte_uniter_transaction']
                qte_gros = vente['qte_gros_transaction']
                if qte_uniter > maxUniter or qte_gros > produit.qte_gros or qte_uniter > produit.qte_uniter :
                    return Response({"message" : 'la quantité est invalide'}, status=status.HTTP_400_BAD_REQUEST)
                if qte_uniter > 0 :
                    produit.qte_uniter -= qte_uniter
                if qte_gros > 0 :
                    produit.qte_gros -= qte_gros
                venteInstance = VenteProduct(
                    product = produit,
                    # vendeur
                    qte_uniter_transaction = qte_uniter,
                    qte_gros_transaction = qte_gros,
                    type_transaction = "Vente",
                    facture = facture
                )
                produit.save()
                prix_uniter = qte_uniter * produit.prix_uniter
                prix_gros = qte_gros * produit.prix_gros
                
                venteInstancList.append(venteInstance)
                
            facture.prix_restant = 0
            facture.prix_total = prix_uniter + prix_gros
            facture.save()

            if len(venteInstancList)>0:   
                VenteProduct.objects.bulk_create(venteInstancList)
                return Response({'message' : "Success"}, status=status.HTTP_201_CREATED)
            else :
                return Response({'message' : "Error de creation"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            raise e

class ListFacture(generics.ListAPIView):
    queryset = Facture.objects.all()
    serializer_class = FactureSerialiser