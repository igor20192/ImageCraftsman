from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import UserProfile, CustomSubscriptionPlan


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            subscription_plan = CustomSubscriptionPlan.objects.get(name="Basic")
            UserProfile.objects.create(
                user=instance, subscription_plan=subscription_plan
            )
        except Exception as e:
            raise e
