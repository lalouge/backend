from django.utils import timezone
from django.conf import settings
from django.db import models

from accounts.models.users import User
from accounts.models.devices import Device, DeviceToken, DeviceTokenBlacklist

from utilities import response

from rest_framework_simplejwt.tokens import RefreshToken

import datetime
import jwt, hashlib


class UserAuthToken:
    def __init__(self, user: User) -> tuple:
        self.user = user

    def get_token_pair(self):
        # Generate access and refresh tokens for the user
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Calculate token expiration times
        current_time = timezone.now()

        # Access token expiration period
        access_token_exp = datetime.datetime.fromtimestamp(refresh.access_token.payload['exp'], tz=timezone.utc)

        # Use Unless There's A Counter (Time Counter) At The Level Of The Frontend
        access_token_exp_seconds = (access_token_exp - current_time).total_seconds()

        # Refresh token expiration period
        refresh_token_exp = datetime.datetime.fromtimestamp(refresh.payload['exp'], tz=timezone.utc)
        
        # Use Unless There's A Counter (Time Counter) At The Level Of The Frontend
        refresh_token_exp_seconds = (refresh_token_exp - current_time).total_seconds()

        return [access_token, access_token_exp], [refresh_token, refresh_token_exp]


class DeviceAuthenticator:
    def __init__(self, secret_key=settings.DEVICE_JWT["SIGNING_KEY"], 
                 access_token_lifetime=settings.DEVICE_JWT["ACCESS_TOKEN_LIFETIME"], 
                 refresh_token_lifetime=settings.DEVICE_JWT["REFRESH_TOKEN_LIFETIME"],
                 database_actions=True, instance: Device = None):
        
        self.secret_key = secret_key
        self.access_token_lifetime = access_token_lifetime
        self.refresh_token_lifetime = refresh_token_lifetime
        self.database_actions = database_actions
        self.instance = instance

    def perform_database_actions(self, access_token, refresh_token, access_token_expires_at,
                                 refresh_token_expires_at):
        
        try:
            device_token_instance = DeviceToken.objects.create(access_token=access_token, refresh_token=refresh_token,
                                                            access_token_expires_at=access_token_expires_at,
                                                            refresh_token_expires_at=refresh_token_expires_at)
            
            self.instance.tokens = device_token_instance

            self.instance.save()
        
        except Exception as e:
            return f"{str(e)} {type(access_token_expires_at)}"
        
        return not None

    def generate_tokens(self):
        # Combine device ID and current timestamp for added uniqueness
        unique_identifier = f"{self.instance.pk}-{datetime.datetime.utcnow().timestamp()}"

        # Hash the unique identifier to generate a token
        token = hashlib.sha256(unique_identifier.encode()).hexdigest()

        # Calculate token expiration times
        current_time = timezone.now()
        access_token_exp = current_time + self.access_token_lifetime
        refresh_token_exp = current_time + self.refresh_token_lifetime

        # Define the payload for both access and refresh tokens
        access_payload = {
            'device_id': self.instance.pk,
            'token': token,
            'exp': access_token_exp
        }

        refresh_payload = {
            'device_id': self.instance.pk,
            'token': token,
            'exp': refresh_token_exp
        }

        # Generating both access and refresh tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])
        access_token_exp_seconds = (access_token_exp - current_time).total_seconds()

        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])
        refresh_token_exp_seconds = (refresh_token_exp - current_time).total_seconds()

        if self.database_actions:
            self.perform_database_actions(
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=access_token_exp,
                refresh_token_expires_at=refresh_token_exp
            )

        return [access_token, access_token_exp_seconds], [refresh_token, refresh_token_exp_seconds]

    def verify_access_token(self, access_token):
        try:
            # Decode and verify the access token
            payload = jwt.decode(access_token, self.secret_key, algorithms=[settings.DEVICE_JWT["ALGORITHM"]])
            return payload
        
        except jwt.ExpiredSignatureError as e:

            self.blacklist_access_token(access_token)

            # Raising errors
            response.errors(
                field_error="Token Has Expired. Revoking Token ...",
                for_developer=f"{str(e)}. Request For New Token",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        except jwt.InvalidTokenError as e:
            # Raising errors
            response.errors(
                field_error="Invalid Token",
                for_developer=f"{e}",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )
        
    def blacklist_access_token(self, access_token):
        DeviceTokenBlacklist.objects.create(access_token=access_token)

        return

    def revoke_refresh_token(self, refresh_token):
        # In a real system, you might want to maintain a list/database of revoked tokens
        # Here, we'll just print a message indicating token revocation
        print(f"Revoking refresh token: {refresh_token}")

    def get_access_token_from_refresh_token(self, refresh_token):
        try:
            # Decode and verify the refresh token
            refresh_payload = jwt.decode(refresh_token, self.secret_key, algorithms=[settings.DEVICE_JWT["ALGORITHM"]])
            
            # Check if the refresh token is still valid
            if datetime.datetime.utcnow() < datetime.datetime.utcfromtimestamp(refresh_payload['exp']):
                # Revoke the used refresh token
                self.revoke_refresh_token(refresh_token)
                
                # Generate a new access token
                new_access_token_payload = {
                    'device_id': refresh_payload['device_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.access_token_lifetime)
                }
                new_access_token = jwt.encode(new_access_token_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])
                
                # Generate a new refresh token
                new_refresh_token_payload = {
                    'device_id': refresh_payload['device_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.refresh_token_lifetime)
                }
                new_refresh_token = jwt.encode(new_refresh_token_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])

                return new_access_token, new_refresh_token
            else:
                print("Refresh token has expired")
                return None, None
        except jwt.InvalidTokenError:
            print("Invalid refresh token")
            return None, None