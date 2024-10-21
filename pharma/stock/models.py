from typing import Iterable
from django.db import models
from django.utils.timezone import localtime
import pytz

from account.models import CustomUser
# Create your models here.


class Fournisseur(models.Model):
    nom = models.CharField(max_length=20, unique=True)
    adress = models.TextField(max_length=25)
    contact = models.CharField(max_length=20)
    
    def __str__(self) -> str:
        return str(self.nom)

    def save(self, *args, **kwargs):
        self.nom = self.nom.upper()
        self.contact = self.contact.replace(' ', '')
        super(Fournisseur, self).save(*args, **kwargs)

class Trosa(models.Model):
    owner = models.CharField(max_length=25)
    date = models.DateField(auto_now_add = True)
    adress = models.TextField(blank=True)
    contact = models.CharField(max_length=20, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=0)
    montant_restant = models.DecimalField(max_digits=10, decimal_places=0)
    
class Facture(models.Model):
    date = models.DateTimeField(auto_now_add=True, null = True)
    prix_total = models.DecimalField(max_digits=10, decimal_places=0)
    prix_restant = models.DecimalField(max_digits=10, decimal_places=0)
    client = models.CharField(max_length=20, default="", blank=True)
    owner = models.ForeignKey(CustomUser, default=1, on_delete=models.CASCADE, related_name="%(class)s_related")

    def __str__(self) -> str:
        return str(self.id)
    
    @property
    def formated_date(self):
        timezone = pytz.timezone('Etc/GMT-3')
        date =  localtime(self.date, timezone) # localtime change the timezone ou la fuseau horaire avec pytz
        formated = date.strftime("%d/%m/%Y, %H:%M") # Formate la date en string et format
        return formated
     
class Transaction(models.Model):
    qte_uniter_transaction = models.IntegerField()
    qte_gros_transaction = models.IntegerField(default=0, null=True)
    type_transaction = models.TextField(max_length=25)
    prix_total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.type_transaction

    class Meta():
        abstract = True

class AjoutStock(Transaction):
    # Vue que ray iany gestionnares ts mila nasina ForegnKey AjoutStock
    gestionnaire = models.ForeignKey(CustomUser, default=1, on_delete=models.CASCADE, related_name="%(class)s_related")

class Marque(models.Model):
    nom = models.CharField(max_length=50)
    provenance = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.nom

class Detail(models.Model):
    designation = models.CharField(max_length=255)
    famille = models.CharField(max_length=24)
    classe = models.CharField(max_length=24)
    type_uniter = models.CharField(max_length=25)
    type_gros = models.CharField(max_length=25)
    qte_max = models.IntegerField(default=0, null=False)

    def __str__(self) -> str:
        return f"{self.designation}"

from django.db.models.constraints import UniqueConstraint
class Product(models.Model):
    prix_gros = models.DecimalField(max_digits=10, decimal_places=0)
    prix_uniter = models.DecimalField(max_digits=10, decimal_places=0)
    qte_uniter = models.IntegerField(default=0, null=True)
    qte_gros = models.IntegerField(default=0, null=True)
    date_peremption = models.DateField()
    date_ajout = models.DateTimeField(auto_now_add=True) 
    ajout_stock = models.ForeignKey(AjoutStock, on_delete=models.SET_NULL, null=True, related_name="%(class)s_related")
    detail = models.ForeignKey(Detail, on_delete=models.CASCADE, default=None, related_name="%(class)s_related")
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE, related_name="%(class)s_related")
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE, related_name="%(class)s_related") 

    class Meta:
        constraints = [
            UniqueConstraint(fields = ['fournisseur', 'marque', 'detail'], name="unique_fournisseur_marque_detail"),
        ]
        
    def __str__(self) -> str:
        return f"{self.detail.designation} + {self.qte_uniter}"

class VenteProduct(Transaction):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name="%(class)s_related")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="%(class)s_related")
    