
from rest_framework import serializers

from .models import CustomUser

class CustomUserSerialiser(serializers.ModelSerializer):
    username = serializers.CharField(max_length = 25)
    password = serializers.CharField()
    account_type = serializers.ChoiceField(
        [
            ("vendeurs", "vendeurs"),
            ("gestionnaires", "gestionnaires")
        ],
        allow_blank = True,
        required=False
    )

    class Meta():
        model = CustomUser
        fields = ['username', 'password', 'account_type']