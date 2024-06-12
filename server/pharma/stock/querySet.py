from datetime import timedelta
from django.utils import timezone
from rest_framework.generics import GenericAPIView
from .models import Product
class ProductQsField(GenericAPIView):
    qs_expired = "expired"

    def get_queryset(self):
        qs = super().get_queryset()
        try:
            expired = self.kwargs[self.qs_expired]
            if expired == "expired":
                today = timezone.now().date()
                three_months_from_now = today + timedelta(days=90)
                print(three_months_from_now)
                qs = Product.objects.filter(date_peremption__lte=three_months_from_now, date_peremption__gte=today)
                return qs
        except Exception as e:
            print(e)
            return qs    
