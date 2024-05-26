from django.db import models
from django.utils import timezone

from account.models import CustomUser
# Create your models here.

class Transaction(models.Model):
    qte_uniter_transaction = models.IntegerField()
    qte_gros_transaction = models.IntegerField(default=0, null=True)
    type_transaction = models.TextField(max_length=25)
    date = models.DateTimeField(timezone.now())

    def __str__(self) -> str:
        return self.type_transaction

    class Meta():
        abstract = True

class AjoutStock(Transaction):
    complete = models.BooleanField(default=False)
    reste = models.DecimalField(max_digits=10, decimal_places=0)
    gestionnaire = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="%(class)s_related")

class Fournisseur(models.Model):
    nom = models.TextField(max_length=20)
    adress = models.TextField(max_length=25)

class Detail(models.Model):
    designation = models.CharField(max_length=255)
    famille = models.CharField(max_length=24)
    classe = models.CharField(max_length=24)
    type_uniter = models.CharField(max_length=25)
    type_gros = models.CharField(max_length=25)
    marque =  models.CharField(max_length=25)
    qte_max = models.IntegerField(default=0, null=False)

    def __str__(self) -> str:
        return f"{self.designation} - {self.famille} - {self.qte_max} "


class Product(models.Model):
    prix_gros = models.DecimalField(max_digits=10, decimal_places=0)
    prix_uniter = models.DecimalField(max_digits=10, decimal_places=0)
    qte_uniter = models.IntegerField(default=0, null=True)
    qte_gros = models.IntegerField(default=0, null=True)
    date_peremption = models.DateField()
    date_ajout = models.DateTimeField(default=timezone.now, null = True) 
    detail = models.ForeignKey(Detail, on_delete=models.CASCADE, default=None, related_name="%(class)s_related")
    ajout_stock = models.ForeignKey(AjoutStock, on_delete=models.SET_NULL, null=True, related_name="%(class)s_related")

    def __str__(self) -> str:
        return f"{self.detail.designation} + {self.qte_uniter}"

class VenteStock(Transaction):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="%(class)s_related")
    vendeur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="%(class)s_related")
    

