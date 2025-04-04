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


     

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
class Reglement(models.Model):
    # Référence générique
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    cible = GenericForeignKey('content_type', 'object_id')  # Peut pointer vers une Facture ou une Trosa

    date_paiement = models.DateTimeField(auto_now_add=True)
    montant = models.DecimalField(max_digits=10, decimal_places=0)
    moyen_paiement = models.CharField(max_length=50, blank=True, default="Espèces")
    # note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Règlement de {self.montant} pour {self.cible}"

class Trosa(models.Model):
    owner = models.CharField(max_length=25)
    date = models.DateField(auto_now_add = True)
    adress = models.TextField(blank=True)
    contact = models.CharField(max_length=20, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=0)
    montant_restant = models.DecimalField(max_digits=10, decimal_places=0)
    reglements = GenericRelation(Reglement)

    
class Facture(models.Model):
    date = models.DateTimeField(auto_now_add=True, null = True)
    prix_total = models.DecimalField(max_digits=10, decimal_places=0)
    prix_restant = models.DecimalField(max_digits=10, decimal_places=0)
    client = models.CharField(max_length=20, default="", blank=True)
    owner = models.ForeignKey(CustomUser, default=1, on_delete=models.CASCADE, related_name="%(class)s_related")
    reglements = GenericRelation(Reglement)

    def __str__(self) -> str:
        return str(self.id)
    
    @property
    def formated_date(self):
        timezone = pytz.timezone('Etc/GMT-3')
        date =  localtime(self.date, timezone) # localtime change the timezone ou la fuseau horaire avec pytz
        formated = date.strftime("%d/%m/%Y, %H:%M") # Formate la date en string et format
        return formated

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
    qte_max_unit = models.IntegerField(default=0, null=False)

    def __str__(self) -> str:
        return f"{self.designation}"

from django.db.models.constraints import UniqueConstraint
class Product(models.Model):
    prix_gros = models.DecimalField(max_digits=10, decimal_places=0)
    prix_detail = models.DecimalField(default = 0, max_digits=10, decimal_places=0, null=True)
    prix_unit = models.DecimalField(default = 0, max_digits=10, decimal_places=0, null=True)
    qte_detail = models.IntegerField(default=0, null=True)
    qte_gros = models.IntegerField(default=0, null=True)
    qte_unit = models.IntegerField(default=0, null=True, blank=True)
    date_peremption = models.DateField()
    date_ajout = models.DateTimeField(auto_now_add=True) 
    # ajout_stock = models.ForeignKey(AjoutStock, on_delete=models.SET_NULL, null=True, related_name="%(class)s_related")
    detail = models.ForeignKey(Detail, on_delete=models.CASCADE, default=None, related_name="%(class)s_related")
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE, related_name="%(class)s_related")
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE, related_name="%(class)s_related") 

    class Meta:
        constraints = [
            UniqueConstraint(fields = ['fournisseur', 'marque', 'detail'], name="unique_fournisseur_marque_detail"),
        ]
        
    def __str__(self) -> str:
        return f"{self.detail.designation} + {self.qte_detail}"

class Transaction(models.Model):
    qte_detail_transaction = models.IntegerField(default=0, null=True)
    qte_gros_transaction = models.IntegerField(default=0, null=True)
    qte_unit_transaction = models.IntegerField(default=0, null = True)
    type_transaction = models.TextField(max_length=25)
    prix_total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    date = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="%(class)s_related")

    def __str__(self) -> str:
        return self.type_transaction

    class Meta():
        abstract = True
        
class AjoutStock(Transaction):
    # Vue que ray iany gestionnares ts mila nasina ForegnKey AjoutStock
    gestionnaire = models.ForeignKey(CustomUser, default=1, on_delete=models.CASCADE, related_name="%(class)s_related")


class VenteProduct(Transaction):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name="%(class)s_related")
    