
from .permissions import IsGestionnaire
from rest_framework.permissions import IsAuthenticated


class GestionnaireEditorMixin():
    permission_classes = [IsAuthenticated, IsGestionnaire]