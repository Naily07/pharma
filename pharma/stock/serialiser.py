from rest_framework import serializers

from .models import *
from django.utils import timezone


class ProductSerialiser(serializers.ModelSerializer):
    prix_uniter = serializers.DecimalField(max_digits=10, decimal_places=0)
    prix_gros = serializers.DecimalField(max_digits=10, decimal_places=0)
    qte_uniter = serializers.IntegerField()
    qte_gros = serializers.IntegerField()
    date_peremption = serializers.DateField()
    date_ajout = serializers.DateTimeField(read_only = True) 
    detail_product = serializers.SerializerMethodField()
    detail_data = serializers.DictField(write_only = True)
    
    class Meta():
        model = Product
        fields = ['prix_uniter', 'prix_gros', 'qte_uniter', 'qte_gros', 'date_ajout', 'date_peremption', 'detail_product', 'detail_data']

    def get_detail_product(self, obj):
        detail = obj.detail
        return f"{detail.designation} - {detail.qte_max}"
    
    def create(self, validated_data):
        detail_data = validated_data.pop("detail_data")
        print(validated_data)
        instance, created = Detail.objects.get_or_create(
            designation=detail_data['designation'], 
            famille=detail_data['famille'], 
            classe=detail_data['classe'], 
            type_uniter=detail_data['type_uniter'], 
            type_gros=detail_data['type_gros'],
            marque=detail_data['marque'],
            qte_max = detail_data['qte_max']
        )
        print("isCreated", created)
        print(instance)
        
        return Product.objects.create(detail = instance, **validated_data)

class DetailSerialiser(serializers.ModelSerializer):
    designation = serializers.CharField(max_length=50, min_length=10, trim_whitespace=True, required = True)
    famille = serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    classe = serializers.CharField(max_length=50, min_length=10, trim_whitespace=True)
    type_uniter = serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    type_gros = serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    marque =  serializers.CharField(max_length=25, min_length=10, trim_whitespace=True)
    qte_max = serializers.IntegerField()

    class Meta():
        model = Detail
        fields = ['designation', 'famille', 'classe', 'type_uniter', 'type_gros', 'marque', 'qte_max']
