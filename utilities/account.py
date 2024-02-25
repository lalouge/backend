from accounts.models.users import User
from accounts.models.account import (PhoneNumberVerificationOTP, UsedOTP, OTPModels)

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db import models

from rest_framework_simplejwt.tokens import RefreshToken

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from utilities import response
from utilities.models.relationship_checker import ModelRelationshipChecker
from utilities.tasks import send_email_task, send_sms_task


class Verification:
    def __init__(self, user: User, model: models.Model = PhoneNumberVerificationOTP):
        self.user = user
        self.model = model

    def email(self) -> bool:

        try:
            model_otp_instance = self.model.objects.get(user=self.user)
        except self.model.DoesNotExist:
            field_message = "OTP Was Not Created For This User"
            for_developer = f"OTP For Corresponding Model ({self.model}) Was Not Created For User ({self.user.username})"

            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer,
                            code="SERVER_ERROR", status_code=1011, main_thread=False, param=self.user.pk)

        # Send email with reset password link
        subject = "LaLouge | Confirm Email Address - Activate Account"

        message = render_to_string('email/email-verification.html', {
            "otp": model_otp_instance.current_otp.otp
        })

        recipient_list = [self.user.email]

        try:
            send_email_task.delay(subject=subject, message=message, recipient_list=recipient_list)
        except Exception as e:
            # setting error messages for user and developer respectively
            field_message = "Failed To Send Email For Verification"
            for_developer = str(e)
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer,
                            code="SERVER_ERROR", status_code=1011, main_thread=False, param=self.user.pk)
        
    
    def phone(self) -> bool:
        sub_id = "Verify Phone Number"

        try:
            model_otp_instance = self.model.objects.get(user=self.user)
        except self.model.DoesNotExist:
            field_message = "OTP Was Not Created For This User"
            for_developer = f"OTP For Corresponding Model ({self.model}) Was Not Created For User ({self.user.username})"

            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer,
                            code="SERVER_ERROR", status_code=1011, main_thread=False, param=self.user.pk)

        message = f"OTP {model_otp_instance.current_otp.otp}"

        try:
            send_sms_task.delay(sub_id=sub_id, message=message, phone=self.user.phone)
        except Exception as e:
            # setting error messages for user and developer respectively
            field_message = "Failed To Send SMS For Verification"
            for_developer = str(e)
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer,
                            code="SERVER_ERROR", status_code=1011, main_thread=False, param=self.user.pk)
    

class OTP:
    def __init__(self, otp: str = None, user: User = None, model: models.Model = PhoneNumberVerificationOTP, database_actions=False):
        self.otp = otp
        self.user = user
        self.model = model
        self.database_actions = database_actions

    def is_valid(self):

        # 
        if self.otp is None or self.user is None:
            # Raising errors
            response.errors(
                field_error = "Internal Server Error. Contact Support.",
                for_developer = f"`otp` And/Or `user` Attribute Value in {self} Should Not Be None.",
                code = "INTERNAL_SERVER_ERROR",
                status_code = 500
            )

        # Checking model validity
        if not self._check_model_validity():
            # Raising errors
            response.errors(
                field_error ="Invalid Model",
                for_developer =f"Model ({self.model._meta.model_name}) Not A Valid Model For This Operation. Valid Models Are {dir(OTPModels)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        model_instances = self.model.objects.filter(user=self.user)

        if not model_instances.exists():
            # setting error messages for user and developer respectively
            field_message = "Internal Server Error. Contact Support"
            for_developer = f"{self.user} Is Not Attributed To Any{self.model._meta.model_name}. Probably Error Occured During Creation Of User Process Or A Dev Must Have Tampered With The GenerateOTP Function In utilities/generators/otp.py"

            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="INTERNAL_SERVER_ERROR", status_code=500)
        
        elif model_instances.count() > 1:
            # setting error messages for user and developer respectively
            field_message = "Internal Server Error. Contact Support"
            for_developer = f"{self.user} Is Attributed To More Than One {self.model._meta.model_name}. Check User Model Relationship With {self.model._meta.model_name}, It Must Be A OneToOne Relationship Else You'll Keep Receiving This Error"

            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="SERVER_ERROR", status_code=500)
        
        # Avoiding QuerySet Value Instance
        model_instance = model_instances.first()

        if model_instance.current_otp:
            if not self.database_actions:
                return self.otp == model_instance.current_otp.otp

            if self.otp and self.otp != model_instance.current_otp.otp:
                return False
        else:
            return False
        
        self.perform_database_actions(model_instance=model_instance)

        try:
            send_sms_task.delay(sub_id="Verify Phone Number", message="Congratulations. Phone Number Verified", phone=self.user.phone)
        except Exception as e:
            # setting error messages for user and developer respectively
            field_message = "Failed To Send SMS For Verification"
            for_developer = str(e)
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        return True

    def perform_database_actions(self, model_instance):
        otp_instance = model_instance.current_otp

        check_relationship = self._relationship_checker()

        if check_relationship[0] == True and check_relationship[2] == models.ForeignKey.__name__:
            field_name = check_relationship[1]
        
        else:
            # Raising errors
            response.errors(
                field_error = "Relationship Nonexistent",
                for_developer = f"Model ({self.model._meta.model_name}) Has No Relationship With {OTP._meta.model_name} or Model ({self.model._meta.model_name}) Is Not A ForeignKey To {OTP._meta.model_name}",
                code = "BAD_REQUEST",
                status_code = 400
            )
        
        # Creating a dictionary with the dynamic field name and value
        update_dict = {"otp": otp_instance, field_name: model_instance}

        # Updating instances based on the dynamic field name
        UsedOTP.objects.filter(**update_dict).update(is_active=False)

        model_instance.current_otp = None
        model_instance.save()

        return

    
    def _check_model_validity(self):
        return any(isinstance(self.model, getattr(OTPModels, model_name)) for model_name in dir(OTPModels))
    
    def _relationship_checker(self):
        checker = ModelRelationshipChecker()
        has_relationship, field_name, relationship_type = checker.check_relationship(
            target_model_name=self.model._meta.model_name, potential_relationship_model_name='UsedOTP',
            app_label=self.model._meta.app_label, relationship_type=models.ForeignKey
        )

        return has_relationship, field_name, relationship_type


class Password:
    def __init__(self, user:User):
        self.user = user

    def reset(self) -> bool:
        redirect_url = "hello"

        refresh = RefreshToken.for_user(self.user)
        reset_password_token = urlsafe_base64_encode(force_bytes(f'{self.user.pk}-{str(refresh.access_token)}'))

        # using the value of the `absolute_uri` value to create the referral link
        reset_password_url = f"{redirect_url}?reset-password-token={reset_password_token}"

        # Send email with reset password link
        subject = 'Password reset'

        message = render_to_string('email/forgot-password.html', {
            'reset_password_url': reset_password_url
        })

        from_email = "ramsesnjasap11@example.com"
        recipient_list = [self.user.email]

        try:
            email_status = send_mail(subject, message, from_email, recipient_list, html_message=message)
        except Exception as e:

            # setting error messages for user and developer respectively
            field_message = "Failed To Send Email For Verification"
            for_developer = str(e)
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)