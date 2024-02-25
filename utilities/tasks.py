# your_app/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import json, requests


@shared_task
def send_email_task(subject: str, message: str, recipient_list: list):
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, recipient_list, html_message=message)


@shared_task
def send_sms_task(sub_id: str, message: str, phone: str):
    url = "https://smsvas.com/bulk/public/index.php/api/v1/sendsms/"

    payload = json.dumps({
        "user": settings.SMS_USER,
        "password": settings.SMS_PASSWORD,
        "senderid": f"LaLouge - {sub_id}",
        "sms": message,
        "mobiles": str(phone).replace("+", "")
    })
    headers = {
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload)