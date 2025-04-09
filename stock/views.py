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
from api.mixins import userFactureQs
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
# Create your views here.
class CreateDetail(generics.ListCreateAPIView): 
    queryset = Detail.objects.all()
    serializer_class = DetailSerialiser
    
class ListProduct(generics.ListAPIView, ProductQsField):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    # qs_field_expired = "expired"
    # qs_rupture = "rupture"
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
        prix_detail = 0
        prix_gros = 0

        try:
            with transaction.atomic():
                for newProduct in productList:
                    if newProduct:
                        detail = newProduct.pop('detail')
                        marque = newProduct.pop('marque')
                        fournisseur = newProduct.pop('fournisseur')
                        detailInstance, createdD = Detail.objects.get_or_create(
                            designation=detail['designation'], 
                            famille=detail['famille'], 
                            classe=detail['classe'], 
                            type_uniter=detail['type_uniter'], 
                            type_gros=detail['type_gros'],
                            qte_max=detail['qte_max'],
                            qte_max_unit=detail['qte_max_unit']
                        )

                        marqueInstance, createdM = Marque.objects.get_or_create(nom=marque)
                        fournisseurInstance, createdF = Fournisseur.objects.get_or_create(
                            nom=fournisseur['nom'].upper(),
                            defaults={
                                'adress': fournisseur['adress'],
                                'contact': fournisseur['contact']
                            }
                        )
                        
                        productExist = Product.objects.filter(
                            detail=detailInstance, marque=marqueInstance, fournisseur=fournisseurInstance
                        ).first()

                        new_qte_gros = newProduct['qte_gros']
                        new_qte_detail = newProduct['qte_detail']
                        if newProduct['qte_unit'] != 0:
                                while newProduct['qte_unit'] > detailInstance.qte_max_unit:
                                    new_qte_detail += 1
                                    newProduct['qte_unit'] -= detailInstance.qte_max_unit
                        if newProduct['qte_detail'] != 0:
                            while newProduct['qte_detail'] > detailInstance.qte_max:
                                new_qte_gros += 1
                                newProduct['qte_detail'] -= detailInstance.qte_max
                            newProduct['qte_gros'] = new_qte_gros

                        if productExist:
                            if int(newProduct['prix_detail']) and int(newProduct['prix_detail']) > 0:
                                productExist.prix_detail = int(newProduct['prix_detail']) 
                            if int(newProduct['prix_gros']) and int(newProduct['prix_gros']) > 0:
                                productExist.prix_gros = int(newProduct['prix_gros'])
                            if int(newProduct['prix_unit']) and int(newProduct['prix_unit']) > 0:
                                productExist.prix_unit = newProduct['prix_unit'] 

                            productExist.qte_unit += newProduct['qte_unit']
                            productExist.qte_gros += new_qte_gros
                            productExist.qte_detail += new_qte_detail

                            while productExist.qte_unit >= detailInstance.qte_max:
                                productExist.qte_unit -= detailInstance.qte_max
                                productExist.qte_gros += 1

                            productsToUpdate.append(productExist)

                            addStockInstance = AjoutStock(
                                qte_unit_transaction=newProduct['qte_unit'],
                                qte_gros_transaction=newProduct['qte_detail'],
                                qte_detail_transaction=newProduct['qte_gros'],
                                type_transaction="Maj",
                                prix_gros = productExist.prix_gros,
                                prix_unit = productExist.prix_unit,
                                prix_detail = productExist.prix_detail,
                                prix_total = (int(productExist.prix_detail) * int( newProduct['qte_detail']) 
                                              + int(productExist.prix_unit) * int( newProduct['qte_unit'])
                                              + int(productExist.prix_gros) * int( newProduct['qte_gros'])),
                                product=productExist,
                                gestionnaire=user
                            )
                            addStockListInstance.append(addStockInstance)
                        else:
                            productsToCreate.append(Product(**newProduct, detail=detailInstance, fournisseur=fournisseurInstance, marque=marqueInstance)) 
                        

                if len(productsToUpdate) > 0:
                    Product.objects.bulk_update(productsToUpdate, fields=['prix_detail', 'prix_gros', 'prix_unit', 'qte_unit', 'qte_gros'])
                if len(productsToCreate) > 0:
                    for product in productsToCreate:
                        product.save()

                        addStockListInstance.append(
                            AjoutStock(
                                qte_unit_transaction=product.qte_unit,
                                qte_gros_transaction=product.qte_gros,
                                qte_detail_transaction=product.qte_detail,
                                type_transaction="Ajout",
                                prix_gros = product.prix_gros,
                                prix_unit = product.prix_unit,
                                prix_detail = product.prix_detail,
                                prix_total = (int(product.prix_detail) * int(product.qte_detail) 
                                              + int(product.prix_unit) * int(product.qte_unit) 
                                              + int(product.prix_gros) * int(product.qte_gros)), 
                                product=product,  
                                gestionnaire=user
                            )
                        )


                AjoutStock.objects.bulk_create(addStockListInstance)

                return Response("Success", status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(f'Error {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProduct(GestionnaireEditorMixin, generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    lookup_field = 'pk'

    def patch(self, request, *args, **kwargs):
        datas = request.data
        user = request.user

        with transaction.atomic():
            
            qte_detail = int(datas['qte_detail'])
            qte_gros = int(datas['qte_gros'])
            product = Product.objects.get(pk = datas['pk'])

            AjoutStock.objects.create(
                qte_gros_transaction=qte_detail,
                qte_detail_transaction=qte_gros,
                type_transaction="Maj",
                prix_gros = product.prix_gros,
                prix_unit = product.prix_unit,
                prix_detail = product.prix_detail,
                prix_total = (int(product.prix_detail) * int( qte_detail)
                                + int(product.prix_gros) * int( qte_gros)),
                product=product,
                gestionnaire=user   
            )

            if int(qte_detail)<0 or int(qte_gros)<0:
                return Response({"message" : "Les valeurs ne peuvent pas être negatif"}, status=status.HTTP_400_BAD_REQUEST)
            if int(qte_detail)>0 or int(qte_gros)>0:
                qte_gros += product.qte_gros
                qte_detail += product.qte_detail
                detailInstance = product.detail
                print("Designation", detailInstance.designation)

                while int(qte_detail) > detailInstance.qte_max: 
                            qte_gros += 1
                            qte_detail -= detailInstance.qte_max
                request.data['qte_detail'] = qte_detail
                request.data['qte_gros'] = qte_gros
            else :
                request.data.pop("qte_gros")
                request.data.pop("qte_detail")
                print(request.data)
            
        return super().patch(request, *args, **kwargs)
    
class DeleteProduct(generics.DestroyAPIView, generics.ListAPIView, GestionnaireEditorMixin):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser

class SellProduct(VendeurEditorMixin, generics.ListCreateAPIView):
    queryset = VenteProduct.objects.all()
    serializer_class = VenteProductSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            user = self.request.user
            prix_uniter = 0
            prix_gros = 0
            prix_detail = 0
            produit = Product.objects.filter(id=serializer.validated_data.get('product_id')).first()
            maxUniter = produit.detail.qte_max
            qte_max_detail = produit.detail.qte_max_detail
            qte_uniter = serializer.validated_data.get('qte_uniter_transaction')
            qte_gros = serializer.validated_data.get('qte_gros_transaction')
            qte_detail = serializer.validated_data.get('qte_detail_transaction')
            if qte_uniter > maxUniter or qte_gros > produit.qte_gros or qte_uniter > produit.qte_uniter or qte_detail > qte_max_detail :
                raise ValidationError(detail={"message" : 'la quantité est invalide'})
            if qte_detail > 0:
                # Mbola ts mety alo ty tsis condition QTEMAX
                produit.qte_detail -= qte_detail
            if qte_uniter > 0 :
                produit.qte_uniter -= qte_uniter
                prix_uniter = qte_uniter * produit.prix_uniter
            if qte_gros > 0 :
                produit.qte_gros -= qte_gros
                prix_gros = qte_gros * produit.qte_gros
            produit.save()
            facture = Facture.objects.create(
                prix_total = prix_gros + prix_uniter + prix_detail,
                prix_restant = 0,
                owner = user
            )

            serializer.save(facture = facture)
            instanceP = serializer.instance
        #Capture l'erreur de validation
        except ValidationError as e:
            raise e
        except Exception as e:
            raise BaseException()

class SellBulkProduct(VendeurEditorMixin, generics.ListCreateAPIView):
    queryset = VenteProduct.objects.all()
    serializer_class = VenteProductSerializer
    
    def post(self, request):
        datas = request.data
        client = ""
        user = request.user
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
                    
        venteList = datas
        venteInstancList = []
        
        try:
            with transaction.atomic():
                facture = Facture(
                    prix_total=0,
                    prix_restant=0,
                    owner=user
                )
                prix_unit = 0
                prix_gros = 0
                prix_detail = 0
                
                for vente in venteList:
                    print("Vente", vente)
                    product_id = vente['product_id']
                    try:
                        produit = Product.objects.get(id=product_id)
                    except Product.DoesNotExist:
                        return Response({"message": "Produit introuvable"}, status=status.HTTP_404_NOT_FOUND)
                    
                    maxUnit = produit.detail.qte_max_unit
                    maxDetail = produit.detail.qte_max
                    
                    qteUnitVente = vente['qte_unit_transaction']
                    qteGrosVente = vente['qte_gros_transaction']
                    qteDetailVente = vente['qte_detail_transaction']
                    
                    if qteGrosVente < 0 or qteUnitVente < 0 or qteDetailVente < 0:
                        return Response({"message": "Erreur de quantité de vente"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    qteGrosStock = produit.qte_gros
                    qteUnitStock = produit.qte_unit
                    qteDetailStock = produit.qte_detail
                    restDetail = 0
                    restUnit = 0
                    dividandDetail = 0
                    dividandUnit = 0
                    #CONVERSION
                    if qteUnitVente > 0 and maxUnit == 0 or qteDetailVente > 0 and maxDetail == 0:
                       return Response({"message": "qte unit ou qte detail indisponible"}, status=status.HTTP_400_BAD_REQUEST)  
                    if qteUnitVente >= maxUnit and qteUnitStock != 0:
                        dividandUnit = int(qteUnitVente) // int(maxUnit)
                        restUnit = int(qteUnitVente) % int(maxUnit)
                        qteUnitVente = restUnit
                        qteDetailVente += dividandUnit
                    
                    if qteDetailVente >= maxDetail and qteDetailVente != 0:
                        dividandDetail = int(qteDetailVente) // int(maxDetail)
                        restDetail = int(qteDetailVente) % int(maxDetail)
                        qteDetailVente = restDetail
                        qteGrosVente = dividandDetail
                    
                    #Condition
                    if qteGrosStock >= qteGrosVente:
                        if qteUnitStock < qteUnitVente and maxUnit != 0:
                            if qteDetailStock > 0:
                                qteUnitStock += maxUnit
                                qteDetailStock -= 1
                            elif qteGrosStock > 0:
                                qteGrosStock -= 1
                                qteDetailStock -= 1
                                qteUnitStock += maxUnit
                            else:
                                return Response({"message": "Stock Detail insuffisant"}, status=status.HTTP_400_BAD_REQUEST)
                        
                        if qteUnitStock > 0:
                            print("DETAIL VENTE", qteDetailVente, qteDetailStock, maxDetail)
                            qteUnitStock -= qteUnitVente

                        ## CALCUL Detail
                        if qteDetailStock >= qteDetailVente and maxDetail != 0:
                            qteDetailStock -= qteDetailVente
                        elif qteDetailVente > qteDetailStock or (qteDetailStock == 0 and qteDetailVente > 0):
                            if qteGrosStock > 0:
                                qteDetailStock += maxDetail
                                qteGrosStock -= 1
                                qteDetailStock -= qteDetailVente
                            else:
                                return Response({"message": "Stock insuffisant"}, status=status.HTTP_400_BAD_REQUEST)
                        
                        if qteGrosStock < qteGrosVente:
                            return Response({"message": "Stock insuffisant"}, status=status.HTTP_400_BAD_REQUEST)
                        
                        qteGrosStock -= qteGrosVente
                    else:
                        return Response({"message": 'La quantité est invalide ou dépasse le stock'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    produit.qte_unit = qteUnitStock
                    produit.qte_gros = qteGrosStock
                    produit.qte_detail = qteDetailStock
                    
                    venteInstance = VenteProduct(
                        product=produit,
                        qte_unit_transaction=qteUnitVente,
                        qte_gros_transaction=qteGrosVente,
                        qte_detail_transaction=qteDetailVente,
                        type_transaction="Vente",
                        prix_total=(int(qteUnitVente * produit.prix_unit)
                                     + int(qteDetailVente * produit.prix_detail)
                                       + int(qteGrosVente * produit.prix_gros)),
                        facture=facture,
                    )
                    
                    produit.save()
                    prix_unit += qteUnitVente * produit.prix_unit
                    prix_gros += qteGrosVente * produit.prix_gros
                    prix_detail += qteDetailVente * produit.prix_detail
                    
                    venteInstancList.append(venteInstance)
                
                facture.prix_restant = prixRestant
                facture.prix_total = prix_unit + prix_gros + prix_detail
                facture.client = client
                facture.save()
                
                if len(venteInstancList) > 0:
                    VenteProduct.objects.bulk_create(venteInstancList)
                    factureData = Facture.objects.filter(pk=facture.pk).first()
                    factureDatas = FactureSerialiser(factureData).data
                    return Response(factureDatas, status=status.HTTP_201_CREATED)
                else:
                    return Response({'message': "Erreur de création"}, status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            return Response({"message": "Le produit n'existe pas"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"Erreur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListVente(generics.ListAPIView):
    queryset = VenteProduct.objects.all()
    serializer_class = VenteProductSerializer

class ListTransactions(GestionnaireEditorMixin, generics.ListAPIView):
    queryset = AjoutStock.objects.all()
    serializer_class = AjoutStockSerialiser

class RetrieveTransactions(GestionnaireEditorMixin, generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerialiser
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ajout = instance.ajoutstock_related.all()
        serializer = self.get_serializer(instance)
        ajoutsersialiser = AjoutStockSerialiser(ajout, many = True).data
        return Response(ajoutsersialiser)

##Mbola ts vita
class CancelFacture(VendeurEditorMixin, generics.RetrieveDestroyAPIView):
    queryset = Facture.objects.all()
    serializer_class = FactureSerialiser
    lookup_field = 'pk'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        print("Object to delete", instance)
        listVente = instance.venteproduct_related.all()
        with transaction.atomic():
            try:
                for vente in listVente:
                    product = Product.objects.get(id = vente.product.id)

                    qte_gros_cancel = vente.qte_gros_transaction
                    qte_unit_cancel = vente.qte_unit_transaction
                    qte_detail_cancel = vente.qte_detail_transaction
                    max_detail = product.detail.qte_max
                    max_unit = product.detail.qte_max_unit
                    
                    restUnit = 0
                    dividandDetail = 0
                    dividandUnit = 0
                    new_qte_unit = product.qte_unit + qte_unit_cancel
                    if new_qte_unit > max_unit:
                        dividandUnit = int(new_qte_unit) // int(max_unit)
                        restUnit = int(qteUnitVente) % int(maxUnit)
                        new_qte_unit = restUnit
                        qte_detail_cancel += dividandUnit

                    new_qte_detail = product.qte_detail + qte_detail_cancel
                    if new_qte_detail > max_detail and new_qte_detail != 0:
                            dividandDetail = int(new_qte_detail) // int(max_detail)
                            restDetail = int(new_qte_detail) % int(max_detail)
                            new_qte_detail = restDetail
                            qte_gros_cancel += dividandDetail
                    product.qte_unit = new_qte_unit
                    product.qte_detail = new_qte_detail
                    product.qte_gros += qte_gros_cancel
                    product.save()
                    
                
                self.perform_destroy(instance)
                return Response(status=status.HTTP_200_OK, data=ProductSerialiser(product).data)
            except Product.DoesNotExist:
                return Response({"message": "Produit introuvable"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"message": f"Erreur Serveur {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class ListFacture(generics.ListAPIView, userFactureQs):
    queryset = Facture.objects.all()
    serializer_class = FactureSerialiser
    # permission_classes = [IsAuthenticated, ]
    
class DeleteFacture(generics.DestroyAPIView):
    queryset = Facture.objects.all()
    serializer_class = FactureSerialiser

class UpdateFacture(generics.RetrieveUpdateAPIView):
    queryset = Facture.objects.all()
    serializer_class = FactureSerialiser
    lookup_field = 'pk'
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_prix_restant = instance.prix_restant

        with transaction.atomic():  # Tout est dans une transaction
            # Valider les données avant de les appliquer
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            # Appliquer la mise à jour
            self.perform_update(serializer)

            # Recharger les données mises à jour
            instance.refresh_from_db()
            new_prix_restant = instance.prix_restant
            print("Facture", new_prix_restant)
            new_prix_restant = instance.prix_restant
            montant_regle = old_prix_restant - new_prix_restant
            print("montant regele", montant_regle)
            if montant_regle > 0:
                # Création du règlement (rollback automatique si erreur ici)
                Reglement.objects.create(
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=instance.id,
                    montant=montant_regle
                )

        queryset = self.filter_queryset(self.get_queryset())
        if queryset._prefetch_related_lookups:
            instance._prefetched_objects_cache = {}
            prefetch_related_objects([instance], *queryset._prefetch_related_lookups)

        return Response(serializer.data)
       
# /*** TROSA  ****/
class CreateTrosa(generics.CreateAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser

class ListTrosa(generics.ListAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser

class DeleteTrosa(generics.RetrieveDestroyAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser

class UpdateTrosa(generics.RetrieveUpdateAPIView):
    queryset = Trosa.objects.all()
    serializer_class = TrosaSerialiser

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_prix_restant = instance.montant_restant

        with transaction.atomic():  # Tout est dans une transaction
            # Valider les données avant de les appliquer
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            # Appliquer la mise à jour
            self.perform_update(serializer)

            # Recharger les données mises à jour
            instance.refresh_from_db()
            new_prix_restant = instance.montant_restant
            print("Trosa", new_prix_restant)
            new_prix_restant = instance.montant_restant
            montant_regle = old_prix_restant - new_prix_restant
            print("montant regele", montant_regle)
            if montant_regle > 0:
                # Création du règlement (rollback automatique si erreur ici)
                Reglement.objects.create(
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=instance.id,
                    montant=montant_regle
                )

        queryset = self.filter_queryset(self.get_queryset())
        if queryset._prefetch_related_lookups:
            instance._prefetched_objects_cache = {}
            prefetch_related_objects([instance], *queryset._prefetch_related_lookups)

        return Response(serializer.data)
 
class ListFournisseur(generics.ListAPIView):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerialiser

class UpdateFournisserur(generics.UpdateAPIView):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerialiser