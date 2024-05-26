
from django.urls import path
from .views import CreateListAccount
urlpatterns = [
    path('create-list-user', CreateListAccount.as_view(), name='account-list')
]