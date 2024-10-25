
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

# Create your views here.
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        # print(user.groups.all().first())
        token['account_type'] = user.groups.all().first().name
        access_token = token.access_token
        refresh_token = token
        print(access_token)

        return access_token, refresh_token