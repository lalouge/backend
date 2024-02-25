from accounts.views.account import ConfirmEmailVerificationView, VerificationView

from django.urls import path

app_name = 'account'
urlpatterns = [
    # path('', ConfirmEmailVerificationView.as_view(), name='verifications')
    path("", VerificationView.as_view(), name="verifications")
]