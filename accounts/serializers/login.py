from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models.users import User

from utilities.serializers.fields import EmailOrPhoneSerializer

import re
from rest_framework import serializers
from django.db import models


from rest_framework import serializers
from django.contrib.auth import authenticate

from utilities.generators.tokens import AuthToken

class LoginCredentialSerializer(serializers.Serializer):
    email_or_phone = EmailOrPhoneSerializer()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(write_only=True)

    def validate(self, data):
        email_or_phone = data.get('email_or_phone')
        password = data.get('password')

        # Check if the input is an email or a phone number
        user = User.objects.filter(
            models.Q(email=email_or_phone) | models.Q(phone=email_or_phone)
        ).first()

        if user:
            # Use Django's built-in authentication to check the password
            if authenticate(request=self.context.get('request'), username=user.email, password=password) is None:
                raise serializers.ValidationError("Incorrect password.")
        else:
            raise serializers.ValidationError("User not found.")

        data['user'] = user

        return data



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        phone = attrs.get("phone")
        pin = attrs.get("password")

        pattern = r"^\+[0-9]{7,15}$"
        match = re.match(pattern, phone)

        if match:
            try:
                user = User.objects.get(phone=phone)
            except:
                raise serializers.ValidationError("Phone number does not exist")

            if user and user.check_password(pin):
                refresh = self.get_token(user)
                data = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "phone": phone,
                    "pin": pin
                }
                return data
            raise serializers.ValidationError("Incorrect phone number or pin.")
        else:
            raise serializers.ValidationError("Invalid phone number pattern. Add country code")
