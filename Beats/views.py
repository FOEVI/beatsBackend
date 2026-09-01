from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from Beats.models import Beat
from Beats.serializer import BeatSerializer

class BeatViewSet(ModelViewSet):
    serializer_class = BeatSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    # Fix C-01 : JWTAuthentication verifie la signature du token (HMAC-SHA256
    # avec SECRET_KEY) avant de resoudre request.user. Avant, le role etait
    # lu sur un payload decode avec verify=False -- n'importe qui pouvait
    # fabriquer un token avec role:"Admin" sans connaitre la cle du serveur.
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _role(self):
        # request.user est resolu par JWTAuthentication a partir d'un token
        # dont la signature a ete verifiee -- pas d'un payload arbitraire.
        return getattr(self.request.user, "role", "Visitor")

    def get_queryset(self):
        return Beat.objects.all() if self._role() == "Admin" else Beat.objects.filter(isPublished=True)

    def perform_create(self, serializer):
        if self._role() == "Admin":
            serializer.save()
        else:
            raise PermissionDenied("You do not have permission to create this beat.")

    def perform_update(self, serializer):
        if self._role() == "Admin":
            serializer.save()
        else:
            raise PermissionDenied("You do not have permission to update this beat.")

    def perform_destroy(self, instance):
        if self._role() == "Admin":
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this beat.")