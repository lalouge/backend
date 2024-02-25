from django.db import models
from django.utils import timezone

from accounts.models.users import User

from utilities.generators.string_generators import QueryID

import uuid


class DeviceLoginHistory(models.Model):
    ip_address = models.GenericIPAddressField(protocol='both')
    physical_address = models.JSONField()
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(null=True)


class DeviceTokenBlacklist(models.Model):
    access_token = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # `updated_at` field is not really necessary in a perfectly secured system
    # But, since now system is perfectly secured, we will need it to monitor
    # if there's any change in `instance` values
    # Since there shouldn't be any change in this instances, any change will mean
    # there's an attack

    # If `updated_at` has any value, it means there's something wrong somewhere.
    updated_at = models.DateTimeField(auto_now=True)


class DeviceToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()

    access_token_expires_at = models.DateTimeField()
    refresh_token_expires_at = models.DateTimeField()

    blacklisted_tokens = models.ManyToManyField("DeviceTokenBlacklist")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_refresh_token_expired(self):
        return timezone.now() > self.refresh_token_expires_at
    
    def is_access_token_expired(self):
        return timezone.now() > self.access_token_expires_at
    
    def token_blacklist(self):
        if self.is_access_token_expired():
            blacklisted_token_instance = DeviceTokenBlacklist.objects.create(access_token=self.access_token)
            self.blacklisted_tokens.add(blacklisted_token_instance)


class DeviceWallet(models.Model):
    synced_amount = models.BinaryField()
    amount_in_sync_transition = models.BinaryField()
    unsynced_amount = models.BinaryField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    device_signature = models.TextField(null=True, blank=True)
    is_synced = models.BooleanField(default=True)

    device_info = models.TextField()

    # This records the percentage trust the system has for this device
    trust = models.PositiveSmallIntegerField(default=0)

    wallet = models.OneToOneField(DeviceWallet, null=True, blank=True, on_delete=models.SET_NULL)

    tokens = models.OneToOneField(DeviceToken, null=True, blank=True, on_delete=models.SET_NULL)

    login_history = models.ForeignKey(DeviceLoginHistory, null=True, blank=True, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def sync_and_unsync_device(self):

        if self.is_synced:
            amount_in_sync_transition = self.wallet.amount_in_sync_transition

            if amount_in_sync_transition != 0:
                self.wallet.synced_amount -= amount_in_sync_transition

                self.wallet.save()
                self.is_synced = False
                self.save()
        
        else:
            self.wallet.synced_amount += self.wallet.unsynced_amount
            self.wallet.amount_in_sync_transition = self.wallet.unsynced_amount
            self.wallet.unsynced_amount = 0

            self.wallet.save()

            self.is_synced = True
            self.save()