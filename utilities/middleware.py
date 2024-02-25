# middleware.py
from django.http import (HttpRequest, JsonResponse)
from django.urls import is_valid_path, get_urlconf


class DeviceMetaInfoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):

        meta_info = {
            "ip": request.META.get("REMOTE_ADDR"),
            "host": request.META.get("REMOTE_HOST", None),
            "user-agent": request.META.get("HTTP_USER_AGENT", None),
            "connection": request.META.get("HTTP_CONNECTION", None),
            "content-length": request.META.get("CONTENT_LENGTH", None)
        }

        request.device_meta_info = meta_info
        return self.get_response(request)


class CheckUnmatchedURLMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        # Check if the requested URL matches any defined URL patterns
        if not is_valid_path(path=request.path_info.lstrip("/"), urlconf=get_urlconf()):
            # If no URL pattern matches, return a JSON response with an error message
            data = {'error': 'No matching URL pattern found.'}
            data['endpoint_status'] = 404

            # Include the original response data in the JSON response
            if response.status_code != 404:
                return response
            
            error = {
                "message": {
                    "request": "NOT FOUND",
                    "field": "No matching URL pattern found.",
                },
                "status": {
                    "code": "NOT_FOUND",
                    "status_code": 404
                },
                "developer": f"{request.path_info.lstrip('/')} Does Not Match Any URLs"
            }

            return JsonResponse(error, status=404)

        return response
