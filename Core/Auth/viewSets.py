from rest_framework.throttling import ScopedRateThrottle
from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.viewsets import ViewSet
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status




from Core.Auth.serializers import RegisterSerializer, LoginSerializer
# Create your views here.


class RegisterViewSet(ViewSet):

    
    serializer_class = RegisterSerializer # We now set the serializer with which information that are posted against this endpoint will be serialized
    permission_classes = [permissions.AllowAny,] # This endpoint should be accessible to anyone, Because it is the registration endpoint
    
    http_method_names = ['post'] # Limiting the http method on this endpoint to post method :

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data) # passing the data post through the request to the serializer and saving.

        serializer.is_valid(raise_exception=True) # is a method call used in Django REST framework to validate the data in a serializer and raise an exception if the validation fails
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        res = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return Response({
            "user": serializer.data,
            "refresh": res["refresh"],
            "token": res["access"]
        },
        
        status=status.HTTP_201_CREATED
        )
    

from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    
class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer # We now set the serializer with which information that are posted against this endpoint will be serialized
    permission_classes = [permissions.AllowAny,] # This endpoint should be accessible to anyone, because of curse it is the Login endpoint, where user will be authenticated
    http_method_names = ['post','options'] # Limiting the http method on this endpoint to 'post' method only
    # Fix M-02 : limite de 5 tentatives par minute par IP, pour empecher
    # une attaque brute force sur les mots de passe.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def create(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)

        try: # Let control our eventual errors
            serializer.is_valid(raise_exception=True)

        except TokenError as e:
            raise InvalidToken(e.args[0]) 
        
        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK
        )
    
class RefreshViewSet(ViewSet, TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    