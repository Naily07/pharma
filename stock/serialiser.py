from rest_framework import serializers

from .models import *
from django.utils import timezone
from django.db import IntegrityError, Error
from rest_framework.response import Response
from rest_framework import status
from psycopg2.errors import UniqueViolation
from account.serialisers import CustomUserSerialiser

class FournisseurSerialiser(serializers.ModelSerializer):
    nom = serializers.CharField(max_length=20, required = True)
    adress = serializers.CharField(max_length=25)
    contact = serializers.CharField(max_length=20)

    class Meta:
        model = Fournisseur
        fields = ['nom', 'adress', 'contact']

class DetailSerialiser(serializers.ModelSerializer):
    designation = serializers.CharField(max_length=50, min_length=10, trim_whitespace=True, required = True)
    famille = serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    classe = serializers.CharField(max_length=50, min_length=10, trim_whitespace=True)
    type_uniter = serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    type_gros = serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    qte_max = serializers.IntegerField()

    class Meta():
        model = Detail
        fields = ['designation', 'famille', 'classe', 'type_uniter', 'type_gros', 'qte_max']

from django.core.validators import MinValueValidator
class ProductSerialiser(serializers.ModelSerializer):
    prix_uniter = serializers.DecimalField(max_digits=10, decimal_places=0)
    prix_gros = serializers.DecimalField(max_digits=10, decimal_places=0)
    qte_uniter = serializers.IntegerField(validators = [MinValueValidator(0)])
    qte_gros = serializers.IntegerField(validators = [MinValueValidator(0)])
    date_peremption = serializers.DateField()
    date_ajout = serializers.DateTimeField(read_only = True) 
    
    detail = serializers.DictField(write_only = True)
    detail_product = serializers.SerializerMethodField()
    
    marque_product = serializers.SerializerMethodField()
    marque = serializers.CharField(write_only =True)
    
    fournisseur_product = serializers.SerializerMethodField()
    fournisseur = serializers.DictField(write_only = True)
    
    class Meta():
        model = Product
        fields = [
                'pk', 'prix_uniter', 'prix_gros', 'qte_uniter', 
                  'qte_gros', 'date_ajout', 'date_peremption', 
                  'detail_product', 'detail',"marque_product",
                  'fournisseur', 'fournisseur_product', 'marque'
                  ]

    
    def get_detail_product(self, obj):
        detail = obj.detail
        detailObj = Detail.objects.filter(designation__iexact = detail.designation).first()
        return DetailSerialiser(detailObj).data
    
    def get_marque_product(self, obj):
        marque = obj.marque
        return marque.nom
    
    def get_fournisseur_product(self, obj):
        fournisseur = obj.fournisseur
        return fournisseur.nom
    
    def create(self, validated_data):
        try:
            print(validated_data)
            detail_data = validated_data.pop("detail")
            marque = validated_data.pop('marque')
            fournisseur = validated_data.pop('fournisseur')
            print(validated_data)
            instance, createdD = Detail.objects.get_or_create(
                designation=detail_data['designation'], 
                famille=detail_data['famille'], 
                classe=detail_data['classe'], 
                type_uniter=detail_data['type_uniter'], 
                type_gros=detail_data['type_gros'],
                qte_max = detail_data['qte_max']
            )
            marqueInstance, createdM = Marque.objects.get_or_create(nom = marque)
            fournisseurInstance, createdF = Fournisseur.objects.get_or_create(
                nom = str(fournisseur['nom']).upper()
            )
            print("isCreated Fourniseeur", createdF)
            print(instance)
        
            return Product.objects.create(detail = instance, marque = marqueInstance, fournisseur = fournisseurInstance, **validated_data)
        except UniqueViolation as e:
            raise serializers.ValidationError({"message": "Un produit avec cette combinaison de fournisseur, marque et détail existe déjà."})
        except IntegrityError as e:
            print("eXX", e)
            raise serializers.ValidationError({"message": f"Erreur d'intégrité des données."})
        except Exception as e:
            raise serializers.ValidationError({"message": f"Une erreur inattendue s'est produite: {str(e)}"})


class VenteProductSerializer(serializers.ModelSerializer):
    qte_uniter_transaction = serializers.IntegerField(min_value = 0)
    qte_gros_transaction = serializers.IntegerField(min_value = 0)
    type_transaction = serializers.ChoiceField([
        ('Vente' , 'Vente'),
        ('Ajout', 'Ajout')
    ])
    date = serializers.DateTimeField(read_only = True)
    product_id = serializers.IntegerField(min_value = 0, write_only = True)
    prix_total = serializers.DecimalField(max_digits=10, decimal_places=0)
    product = serializers.SerializerMethodField(read_only = True)
    # vendeur = serializers.SerializerMethodField(read_only = True)
    facture = serializers.SerializerMethodField(read_only = True)

    class Meta():
        model = VenteProduct
        fields = [
            'qte_uniter_transaction', 'qte_gros_transaction', 
            'type_transaction', 'product', 'date',
            'product_id', 'facture', 'prix_total'
            ]

    def get_product(self, obj):
        venteStock = obj
        produit : Product = venteStock.product
        # print(produit.detail)
        return produit.detail.designation
    
    # def get_vendeur(self, obj):
    #     vendeur : CustomUser = obj.vendeur
    #     return vendeur.username
    
    def get_facture(self, obj):
        f : Facture = obj.facture
        return f.id 
    
class FactureSerialiser(serializers.ModelSerializer):
    prix_total = serializers.DecimalField(max_digits=10, decimal_places=0)
    prix_restant = serializers.DecimalField(max_digits=10, decimal_places=0)
    produits = serializers.SerializerMethodField(read_only = True)
    client = serializers.CharField()
    date = serializers.SerializerMethodField(read_only = True)
    owner = serializers.SerializerMethodField(read_only = True)
    class Meta:
        model = Facture
        fields = ['pk', 'prix_total', 'prix_restant', 'produits', 'client', 'date', 'owner']

    def get_produits(self, obj):
        facture = obj
        vente = facture.venteproduct_related.all()
        return VenteProductSerializer(vente, many = True).data 
    
    def get_owner(self, obj):
        owner = CustomUserSerialiser(obj.owner).data
        print(owner)
        return owner['username']
    
    def get_date(self, obj):
        print("Formate", obj.formated_date)
        return obj.formated_date
class TrosaSerialiser(serializers.ModelSerializer):
    owner = serializers.CharField(required = True)
    date = serializers.DateField()
    montant = serializers.DecimalField(max_digits=10, decimal_places=0, read_only = True)
    montant_restant = serializers.DecimalField(max_digits=10, decimal_places=0)
    contact = serializers.CharField(allow_blank = True)
    adress = serializers.CharField(allow_blank = True)
    class Meta:
        model = Trosa
        fields = ["pk", 'owner', 'date', 'montant', 'montant_restant', 'adress', 'contact']
    
    def create(self, validated_data):
        trosa = Trosa.objects.create(montant = validated_data.get('montant_restant'), **validated_data)
        return trosa