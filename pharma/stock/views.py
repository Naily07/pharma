from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView

from api.paginations import StandardResultPageination
from api.mixins import GestionnaireEditorMixin, VendeurEditorMixin
from api.mixins import ProductQsField
from .models import *
from .serialiser import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.permissions import IsGestionnaire
from rest_framework.permissions import IsAuthenticated
# Create your views here.

class CreateDetail(generics.ListCreateAPIView): 
    queryset = Detail.objects.all()
    serializer_class = DetailSerialiser
    
class ListProduct(generics.ListAPIView, ProductQsField):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    qs_field = "expired"
    permission_classes = [IsAuthenticated, ]


class CreateProduct(GestionnaireEditorMixin, generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser

class CreateBulkStock(GestionnaireEditorMixin, APIView):
    # permission_classes = [IsAuthenticated, IsGestionnaire]
    def post(self, request):
        productsToCreate = []
        productsToUpdate = []
        productList = request.data
        user = request.user
        addStockListInstance = []
        prix_uniter = 0
        prix_gros = 0

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
                #Update quantiter et prendre la nouvelle qté dans Transaction
                if productExist:
                    new_qte_gros = newProduct['qte_gros']
                    
                    #Test de quantiter maximum d'uniter
                    while newProduct['qte_uniter'] >= detailInstance.qte_max: 
                        new_qte_gros += 1
                        newProduct['qte_uniter'] -= detailInstance.qte_max

                    productExist.qte_uniter += newProduct['qte_uniter']
                    productExist.qte_gros += new_qte_gros

                    while productExist.qte_uniter >= detailInstance.qte_max:
                        productExist.qte_uniter -= detailInstance.qte_max
                        productExist.qte_gros += 1

                    productsToUpdate.append(productExist)
                    #Instance pour la transaction
                    addStockInstance = AjoutStock(
                        qte_uniter_transaction = newProduct['qte_uniter'],
                        qte_gros_transaction = new_qte_gros,
                        type_transaction = "Ajout",
                        gestionnaire = user
                    )
                    #Ajouter la prix de chaque transaction au facture
                    # prix_gros += int(addStockInstance.qte_gros_transaction) * int(productExist.prix_gros)
                    # prix_uniter += int(addStockInstance.qte_uniter_transaction) * int(productExist.prix_uniter)

                else:
                    productsToCreate.append(Product(**newProduct, detail = detailInstance, fournisseur = fournisseurInstance, marque = marqueInstance)) 
                    #Instance pour chaque transaction
                    addStockInstance = AjoutStock(
                        qte_uniter_transaction = newProduct['qte_uniter'],
                        qte_gros_transaction = newProduct['qte_gros'],
                        type_transaction = "Ajout",
                        gestionnaire = user
                    )
                    # prix_uniter += int(newProduct['qte_uniter']) * int(newProduct['prix_uniter'])
                    # prix_gros += int(newProduct['qte_gros']) * int(newProduct['prix_gros'])
                
                addStockListInstance.append(addStockInstance)
                
                print(f"this {detail} is created {createdD}")
                print(productsToCreate)
                
            
            if len(productsToUpdate)>0:
                Product.objects.bulk_update(productsToUpdate, fields=['prix_uniter', 'prix_gros', 'qte_uniter', 'qte_gros'])
            if len(productsToCreate)>0:
                Product.objects.bulk_create(productsToCreate)

            AjoutStock.objects.bulk_create(addStockListInstance)

            return Response(f"Success", status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(f'Error {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProduct(GestionnaireEditorMixin, generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    lookup_field = 'pk'

    def patch(self, request, *args, **kwargs):
        datas = request.data
        print(datas['pk'])
        qte_uniter = int(datas['qte_uniter'])
        qte_gros = int(datas['qte_gros'])
        print("Gors", qte_gros)
        if int(qte_uniter)>0 or int(qte_gros)>0:
            product = Product.objects.get(pk = datas['pk'])
            qte_gros += product.qte_gros
            qte_uniter += product.qte_uniter
            detailInstance = product.detail
            print("Designation", detailInstance.designation)

            while int(qte_uniter) > detailInstance.qte_max: 
                        qte_gros += 1
                        qte_uniter -= detailInstance.qte_max
        request.data['qte_uniter'] = qte_uniter
        request.data['qte_gros'] = qte_gros

        return super().patch(request, *args, **kwargs)
    

class DeleteProduct(GestionnaireEditorMixin, generics.DestroyAPIView, generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser


class SellProduct(VendeurEditorMixin, generics.ListCreateAPIView):
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

class ListVente(generics.ListAPIView):
    queryset = VenteProduct.objects.all()
    serializer_class = VenteProductSerializer

class SellBulkProduct(VendeurEditorMixin, APIView):
    
    #Transaction des Ventes en Masses
    def post(self, request):
        datas = request.data
        client = ""
        user = request.user
        print("USSS", user)
        prixRestant = 0
        datasCopy = datas.copy()
        for item in datasCopy:
            for key, value in item.items():
                if key == "client":
                    client = value
                    datas.remove(item)
                if key == "prix_restant":
                    prixRestant = value
                    datas.remove(item)
                    
        print("No client data :", datas)
        # print("Client", client)
        venteList = datas
        venteInstancList = []
        try:
            facture = Facture(
                prix_total = 0,
                prix_restant = 0
            )
            prix_uniter = 0
            prix_gros = 0
            #un boucle pour chaque vente
            for vente in venteList:
                # print("Vente", vente)
                product_id = vente['product_id']
                produit = Product.objects.filter(id=product_id).first()
                maxUniter = produit.detail.qte_max
                qteUniterVente = vente['qte_uniter_transaction'] 
                qteGrosVente = vente['qte_gros_transaction'] 
                print("UniterVente", qteUniterVente)
                qteGrosStock = produit.qte_gros
                qteUniterStock = produit.qte_uniter
                # if vente['prix_restant']:
                #     prixRestant += int(vente['prix_restant'])

                if qteGrosStock >= qteGrosVente:
                    if maxUniter >= qteUniterVente :
                        if qteUniterStock >= qteUniterVente :
                            qteUniterStock -= qteUniterVente
                            qteGrosStock -= qteGrosVente

                        elif qteUniterVente > qteUniterStock or (qteUniterStock == 0 and qteUniterVente > 0) :
                            #Cas ou qteUniter en stock == 0 ou uniter en vente > stock
                            qteUniterStock += maxUniter 
                            qteGrosStock -= 1               #Ouvrir une boite et prendre uniter dans la boite, boite non Vendu mais ouvert
                            # qteGrosVente += 1  
                            qteUniterStock -= qteUniterVente

                        else : #uniter vente == 0
                            qteGrosStock -= qteGrosVente

                    elif qteUniterVente <= qteGrosStock * maxUniter :
                        # if qteUniterVente <= maxUniterPossible :
                        while qteUniterVente >= maxUniter:# ouvrir un boite pour chaque boucle
                            qteUniterVente -= maxUniter 
                            # qteGrosStock -= 1 #a la fin la quantité unité en vente est inf max s'il est egale on le considère comme une boite
                            qteGrosVente += 1  

                        if qteUniterStock <= qteUniterVente:#Verfier si en stock peut satisfaire la vente 
                            qteUniterStock += maxUniter
                            qteGrosVente += 1  

                        qteUniterStock -= qteUniterVente
                        qteGrosStock -= qteGrosVente
                    else:
                        return Response({"message" : 'la quantité est invalide ou depasse le stock'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message" : 'la quantité est invalide ou depasse le stock'}, status=status.HTTP_400_BAD_REQUEST)
                
                produit.qte_uniter = qteUniterStock
                produit.qte_gros = qteGrosStock

                venteInstance = VenteProduct(
                    product = produit,
                    # vendeur
                    qte_uniter_transaction = qteUniterVente,
                    qte_gros_transaction = qteGrosVente,
                    type_transaction = "Vente",
                    prix_total = int(qteUniterVente * produit.prix_uniter) + int(qteGrosVente * produit.prix_gros),
                    facture = facture,
                    vendeur = user
                )
                produit.save()
                prix_uniter += qteUniterVente * produit.prix_uniter
                prix_gros += qteGrosVente * produit.prix_gros
                
                venteInstancList.append(venteInstance)

            facture.prix_restant = 0
            facture.prix_total = prix_uniter + prix_gros
            facture.client = client
            facture.prix_restant = prixRestant
            facture.save()

            if len(venteInstancList)>0:   
                VenteProduct.objects.bulk_create(venteInstancList)
                return Response({'message' : "Success"}, status=status.HTTP_201_CREATED)
            else :
                return Response({'message' : "Error de creation"}, status=status.HTTP_400_BAD_REQUEST)
        except AttributeError as e:
            return Response({"message" : "le produit n'existe pas"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise e

class ListFacture(generics.ListAPIView):
    queryset = Facture.objects.all()
    serializer_class = FactureSerialiser

class CreateTrosa(generics.CreateAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser

class ListTrosa(generics.ListAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser

class DeleteTrosa(generics.RetrieveDestroyAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser
 