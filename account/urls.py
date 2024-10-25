
from django.urls import path
from .views import *
urlpatterns = [
    path('register', CreateListAccount.as_view(), name='account-list'),
    path('login', Login.as_view(), name='login'),
]