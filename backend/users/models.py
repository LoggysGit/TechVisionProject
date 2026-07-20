""" Users models """

from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone

class OAuthAccount(models.Model):
    """ System OAuth data """

    # Connect OAuth with user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='oauth_accounts')
    # Provider name
    provider = models.CharField(max_length=50)
    # Provider ID
    provider_user_id = models.CharField(max_length=255, unique=True)
    # Created at
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} via {self.provider}"


class Subscription(models.Model):
    """ Subscription data """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    
    class Status(models.TextChoices):
        """ Subscription status class """
        ACTIVE = 'active', "Active"
        CANCELED = 'canceled', "Cancelled"
        EXPIRED = 'expired', "Expired"
        NONE = 'none', "No subscription"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NONE
    )
    
    class Tier(models.TextChoices):
        """ Subscription tier class """
        FREE = 'free', "Free tier"
        PRO = 'pro', "Pro (Suscription)"

    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.FREE
    )

    start_date = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription {self.tier} for {self.user.email} ({self.status})"
    
    @property
    def is_premium_active(self):
        """ Returns subscriprion status """
        if self.status == self.Status.ACTIVE and self.expires_at:
            return self.expires_at > timezone.now()
        return False