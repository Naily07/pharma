from django.shortcuts import render
from rest_framework import generics

from .serialisers import CustomUserSerialiser
from django.contrib.auth.models import Group
from .models import CustomUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from api.serializers import MyTokenObtainPairSerializer
from rest_framework import status
# Create your views here.


class CreateListAccount(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerialiser

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        try:
            account_type = serializer.validated_data.get('account_type')
            print(account_type)
            group = Group.objects.get(name = f"{account_type}s")
            if group:
                print("GRR", group)
                serializer.save()
            
            user = serializer.instance
            user.groups.add(group)
        except Exception as e:
            raise e

from django.contrib.auth import authenticate
class Login(APIView):
    permission_classes = []
    def post(self, request):
        try :
            print(request)
            username = request.data.get('username')
            password = request.data.get('password')
        except Exception as e:
            raise e
        
        # user =  CustomUser.objects.filter(username__iexact = username, password__iexact = password).first() 
        user = authenticate(request, username = username, password =  password)
        # print("USER", user)
        try :
            if user is None :
                raise AuthenticationFailed("le compte n'existe pas")
            # print(user)
            access_token, refresh_token = MyTokenObtainPairSerializer.get_token(user)
            response = Response()
            response.data = {
                "access_token": f"{access_token}",
                "refresh_token": f"{refresh_token}"
            }
            
            # response.set_cookie('jwt_refresh', refresh)
            response.status_code = status.HTTP_200_OK
            return response  
        
        except Exception as e:
            raise AuthenticationFailed(f"Login error {e}")
