from django.shortcuts import render
from rest_framework import generics

from .serialiser import CustomUserSerialiser

from .models import CustomUser
# Create your views here.


class CreateListAccount(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerialiser
