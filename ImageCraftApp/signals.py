from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from .models import UserProfile, CustomSubscriptionPlan


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a user profile for the new User instance upon creation.

    This signal handler creates a user profile associated with the newly created User instance.
    The user profile is created with a subscription plan set to "Basic" by default.

    Args:
        sender (Model): The model class sending the signal (User in this case).
        instance (User): The instance of the User model being created.
        created (bool): A boolean indicating if the User instance is being created.
        kwargs: Additional keyword arguments.

    Raises:
        ObjectDoesNotExist: If the "Basic" subscription plan is not found.
        Exception: If an unexpected exception occurs during profile creation.
    """
    if created:
        try:
            subscription_plan = get_object_or_404(CustomSubscriptionPlan, name="Basic")
            UserProfile.objects.create(
                user=instance, subscription_plan=subscription_plan
            )
        except ObjectDoesNotExist as e:
            # Handle the case where the "Basic" subscription plan is not found
            raise e
        except Exception as e:
            # Handle any other unexpected exceptions during profile creation
            raise e
