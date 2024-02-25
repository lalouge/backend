from django.conf import settings

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

from accounts.models.users import User
from accounts.models.devices import Device, DeviceToken

from utilities.generators.tokens import DeviceAuthenticator
from utilities import response


class AuthPermission(BasePermission):
    def check_user_active_status(self, request):
        ...
    
    def check_user_verification(self, request):
        ...

    def has_permission(self, request, view):

        # Check if Content-Type is not in request header
        # If it is not in request header, raise appropriate error
        if "Content-Type" not in request.headers:

            response.errors(
                field_error = "The 'Content-Type' header is missing in the request.",
                for_developer = "The 'Content-Type' header is missing in the request.",
                code = "CONTENT_TYPE_MISSING",
                status_code = 401
            )
        
        # Check if Content-Type is `application/json`
        # if it is not `application/json` raise appropriate error
        # Note: It is ideal to use json for API based systems
        if request.headers["Content-Type"] != "application/json":

            response.errors(
                field_error = "The 'Content-Type' header must be set to 'application/json' for this request.",
                for_developer = f"You currently have {request.META.get('CONTENT_TYPE')} as Content-Type value instead of 'application/json'",
                code = "INVALID_CONTENT_TYPE",
                status_code = 400
            )
        
        # Create Authentication class instance
        authentication = IsAuthenticated()

        # User authentication instance to grab 
        has_permission = authentication.has_permission(request, view)

        if not has_permission:
            
            response.errors(
                field_error = "You do not have permission to access this resource.",
                for_developer = f"You do not have permission to perform a `{request.META.get('REQUEST_METHOD')}` method on {request.META.get('PATH_INFO')}.",
                code = "FORBIDDEN_ACCESS",
                status_code = 403
            )
        
        return True


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):

        if "Content-Type" not in request.headers:
            return False

        # Check if the user is authenticated and an admin
        authentication = IsAuthenticated()
        if not authentication.has_permission(request, view):
            return False

        user = request.user
        if not user.is_authenticated or not user.is_staff:
            return False

        return True
    

class DeviceAuthPermission(BasePermission):
    def get_user_by_query_id(self, request):
        query_id = request.GET.get("query-id", None)

        user_instance = User.get_user(query_id=query_id)

        return user_instance

    def validate_device_token(self, request, access_token):
        device_authenticator = DeviceAuthenticator()

        # Checking If Device Access Token Is Valid.
        # If No Errors Are Raised Then It Is Valid
        device_authenticator.verify_access_token(access_token)

        try:
            device_token_instance = DeviceToken.objects.get(access_token=access_token)
        except DeviceToken.DoesNotExist as e:
            response.errors(
                field_error = "Server Error. Contact Support.",
                for_developer = f"{str(e)}",
                code = "SERVER_ERROR",
                status_code = 500
            )
        except Exception as e:
            response.errors(
                field_error = "Server Error. Contact Support.",
                for_developer = f"{str(e)}",
                code = "SERVER_ERROR",
                status_code = 500
            )

        try:
            device_instance = Device.objects.get(tokens=device_token_instance)
        except Device.DoesNotExist as e:
            response.errors(
                field_error = "Server Error. Contact Support.",
                for_developer = f"{str(e)}",
                code = "SERVER_ERROR",
                status_code = 500
            )
        except Exception as e:
            response.errors(
                field_error = "Server Error. Contact Support.",
                for_developer = f"{str(e)}",
                code = "SERVER_ERROR",
                status_code = 500
            )
        
        # Update This To Check For Anonymous User Instead
        if request.user is None:
            response.errors(
                field_error = "User Not Authenticated.",
                for_developer = "User Cannot Be Anonymous. User Authentication (Login) Is Required",
                code = "BAD_REQUEST",
                status_code = 400
            )
        
        user_instance = self.get_user_by_query_id(request=request)

        if device_instance.user != user_instance:
            response.errors(
                field_error = "Device Doesn't Recognise This User.",
                for_developer = f"Every Device Is Assigned To A User. Device Doesn't Recognise This User",
                code = "SERVER_ERROR",
                status_code = 400
            )
        
        return True

    def check_device_authentication_header(self, request):
        if "Device-Authentication" in request.headers:
            header_values = request.headers["Device-Authentication"]

            try:
                header_values = header_values.split(" ")
                token_type = header_values[0]
                access_token = header_values[1]
            
            except Exception as e:
                response.errors(
                    field_error="Error In Getting Device Token",
                    for_developer=f"{str(e)}",
                    code="BAD_REQUEST",
                    status_code=400
                )
            
            if token_type not in settings.DEVICE_JWT["AUTH_HEADER_TYPE"]:
                response.errors(
                    field_error = "Something Went Wrong In Authenticating This Device",
                    for_developer = f"Device Authentication Failed: {token_type} Not Found In {settings.DEVICE_JWT['AUTH_HEADER_TYPE']}",
                    code = "BAD_REQUEST",
                    status_code = 400
                )
            
            is_device_token_validated = self.validate_device_token(request=request, access_token=access_token)

            if is_device_token_validated:
                return True
            
        return False

    def has_permission(self, request, view):

        if "Content-Type" not in request.headers:
            response.errors(
                field_error="The 'Content-Type' header is missing in the Request Header.",
                for_developer="The 'Content-Type' header is missing in the Request Header.",
                code="BAD_REQUEST",
                status_code=400
            )

        else:
            if request.headers["Content-Type"] != "application/json":
                response.errors(
                    field_error="The 'Content-Type' header must be set to 'application/json' for this request.",
                    for_developer="The 'Content-Type' header must be set to 'application/json' for this request.",
                    code="BAD_REQUEST",
                    status_code=400
                )

        check_auth_header = self.check_device_authentication_header(request=request)

        if check_auth_header:
            return True

        response.errors(
            field_error = "This device does not have permission to access this resource.",
            for_developer = f"This device does not have permission to perform a `{request.META.get('REQUEST_METHOD')}` method on {request.META.get('PATH_INFO')}.",
            code = "FORBIDDEN_ACCESS",
            status_code = 403
        )