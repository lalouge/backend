# Import necessary libraries and modules from rest_framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Import models from accounts models
from accounts.models.users import User

# Import serializers from accounts serializer
from accounts.serializers.login import LoginCredentialSerializer

# Import from Python libraries
from datetime import datetime  # For working with date and time
from django.utils import timezone as django_timezone  # Django's timezone handling
from django.utils import timezone
from django.views import View
from django.shortcuts import render
from django.utils.http import urlsafe_base64_decode
from django.urls import reverse
from urllib.parse import urlencode

import requests, threading

from utilities import response
from utilities.permissions import AuthPermission
from utilities.account import Verification
from utilities.response import APIExceptionError
from utilities import response
from rest_framework.parsers import JSONParser



# Login view class that extends from APIView
class LoginAPIView(APIView):

    # Handle HTTP Post method
    def post(self, request):

        # Create user serializer instance using request data and parsing request
        # to serializer class for extra functionality on request
        serializer = LoginCredentialSerializer(data=request.data)

        # Validating is request body (data is valid)
        if serializer.is_valid():

            # Save the user instance to the database
            user_instance = serializer.instance

            # Generate access and refresh tokens for the user
            refresh = RefreshToken.for_user(user_instance)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Calculate token expiration times
            current_time = django_timezone.now()

            # Access token expiration period
            access_token_exp = datetime.fromtimestamp(refresh.access_token.payload['exp'], tz=timezone.utc)
            access_token_exp_seconds = (access_token_exp - current_time).total_seconds()

            # Refresh token expiration period
            refresh_token_exp = datetime.fromtimestamp(refresh.payload['exp'], tz=timezone.utc)
            refresh_token_exp_seconds = (refresh_token_exp - current_time).total_seconds()

            # Perform geolocation lookup asynchronously
            user_ip = request.META.get('REMOTE_ADDR')
            
            # Perform geolocation lookup in a separate thread
            geolocation_thread = threading.Thread(target=self.get_geolocation, args=(user_ip, self.handle_geolocation))
            geolocation_thread.start()
            
            # Determine the verification type
            verification_type = "phone" if user_instance.phone else "email"

            # Set up query parameters and redirect URI
            query_params = {"verify": verification_type}
            redirect_uri = request.build_absolute_uri(reverse("account:verifications") + "?" + urlencode(query_params))

            # Creating a thread for the appropriate verification method
            send_verification_thread = threading.Thread(
                target=getattr(Verification(user=user_instance, redirect_uri=redirect_uri), verification_type)
            )
            send_verification_thread.start()

            # Create the response data
            data = {
                'user': serializer.data,
                'access_token': {
                    'token': access_token,
                    'exp': access_token_exp_seconds
                },
                'refresh_token': {
                    'token': refresh_token,
                    'exp': refresh_token_exp_seconds
                }
            }

            return Response(data, status=status.HTTP_201_CREATED)
        
        # serializer_errors = response.serializer_errors(serializer.errors)

        # If the data is not valid, return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)