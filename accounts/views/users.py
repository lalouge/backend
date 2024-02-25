# Import necessary libraries and modules from rest_framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Import models from accounts models
from accounts.models.users import User
from accounts.models.devices import Device, DeviceLoginHistory
from accounts.models.account import PhoneNumberVerificationOTP, EmailVerificationOTP

# Import serializers from accounts serializer
from accounts.serializers.users import UserSerializer

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
from utilities.generators.tokens import UserAuthToken
from utilities.generators.string_generators import QueryID

from rest_framework.parsers import JSONParser
from rest_framework.pagination import PageNumberPagination

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 1


# User view class that extends from APIView
class UserAPIView(APIView):
    pagination_class = CustomPageNumberPagination

    def check_remember_me_instance(self, remember_me):
        if not isinstance(remember_me, bool):
            response.errors(
                field_error="`remember_me` Field Must Be Boolean",
                for_developer="`remember_me` Field Must Be Boolean",
                code="BAD_REQUEST",
                status_code=400
            )
        
        return

    # Handle HTTP Post method
    def post(self, request):

        remember_me = request.data.pop("remember_me", False)

        self.check_remember_me_instance(remember_me=remember_me)

        # Create user serializer instance using request data and parsing request
        # to serializer class for extra functionality on request
        serializer = UserSerializer(data=request.data, context={'request': request})

        # Validating is request body (data is valid)
        if serializer.is_valid():

            # Save the user instance to the database
            user_instance = serializer.save()

            user_instance._pk_hidden = False
            user_instance.save()

            # Perform geolocation lookup asynchronously
            user_ip = request.device_meta_info["ip"]
            
            # Perform geolocation lookup in a separate thread
            geolocation_thread = threading.Thread(target=self.get_geolocation, args=(user_ip, self.handle_geolocation, user_instance))
            geolocation_thread.start()
            
            # Determining the verification type
            verification_type = ["phone", PhoneNumberVerificationOTP] if user_instance.phone else ["email", EmailVerificationOTP]

            # Creating a thread for the appropriate verification method
            send_verification_thread = threading.Thread(
                target=getattr(Verification(user=user_instance, model=verification_type[1]), verification_type[0])
            )
            send_verification_thread.start()
            
            # Create the response data

            data = {}
            data["user"] = {}
            data["user"]["query_id"] = serializer.data["query_id"]

            data["user"]["storage"] = {}

            data["user"]["storage"]["local"] = remember_me
            data["user"]["storage"]["session"] = not remember_me

            return Response(data, status=status.HTTP_201_CREATED)
        
        # serializer_errors = response.serializer_errors(serializer.errors)

        # If the data is not valid, return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_geolocation(self, user_ip, callback, user_instance):

        try:
            # Perform the geolocation lookup
            url = f"https://ipinfo.io/{user_ip}/json/"
            res = requests.get(url)
            geolocation_data = res.json()
            callback(geolocation_data=geolocation_data, user_instance=user_instance)
        
        # This Error Response Should Use Websocket (Real Time)
        except requests.RequestException as e:

            response.errors(
                field_error="Failure To Get Device GeoLocation Data",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )
        
        except Exception as e:

            print("WHAT ABOUT HERE 2?")

            response.errors(
                field_error="Failure To Get Device GeoLocation Data",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

    def handle_geolocation(self, geolocation_data, user_ip, user_instance):
        # Handle the geolocation data, save it to the database, etc.
        device_instance = Device.objects.create(user=user_instance, device_signature="None", device_info="None",
                              trust=100)
        
        device_login_history_instance = DeviceLoginHistory.objects.create(ip_address=user_ip, physical_address=geolocation_data)

        device_instance.login_history = device_login_history_instance
        device_instance.save()

        # Send data to the frontend through websocket

        data = {}
        data["user"] = {
            "query_id": QueryID().get_query_id(user_instance.query_id)
        }

        user_device_instance = Device.objects.filter(user__query_id=user_instance.query_id).last()

        # If User Device Was Created Successfully, Extract The Device's Token Data
        if user_device_instance:
            tokens = user_device_instance.tokens
            access = {
                "token": tokens.access_token,
                "exp": tokens.access_token_expires_at.isoformat()
            }
            refresh = {
                "token": tokens.refresh_token,
                "exp": tokens.refresh_token_expires_at.isoformat()
            }
        
        else:
            response.errors(
                field_error="Failure To Register Device",
                for_developer="Failure To Register Device",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

        device_data = {}
        device_data["tokens"] = {}
        device_data["tokens"]["access"] = access
        device_data["tokens"]["refresh"] = refresh

        data["user"]["device"] = device_data

        """
        Data To Be Sent To WebSocket Should Be In The Json Format
        {
            "user": {
                "query_id": ***,
                "device": {
                    "tokens": {
                        "access": {
                            "token": ***,
                            "exp": ***
                        },
                        "refresh": {
                            "token": ***,
                            "exp": ***
                        }
                    }
                }
            }
        }

        This Is To Ensure Consistency Throughout The Application.
        Although The User Can Use More Than One Device At The Same Time, Only The
        Tokens For The Device Making The Request Should Be Sent
        """

        channel_layer = get_channel_layer()

        async def send_device_data():
            await channel_layer.group_send(
                f"user_{user_instance.pk}",
                {
                    'type': 'send.device_data',
                    'device_data': data,
                }
            )

        # Convert the asynchronous function to a synchronous one
        async_to_sync(send_device_data)()

        return

    # Define a method that handles GET requests
    def get(self, request):

        # Retrieve all user instances and serialize them for response
        user_instances = User.objects.all()

        serializer = UserSerializer(user_instances, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)