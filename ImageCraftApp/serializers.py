from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Image, UserProfile, CustomSubscriptionPlan


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Image model.
    """

    class Meta:
        model = Image
        fields = ["title", "image", "link_expiration_time"]

    def get_original_file(self, user_id):
        """
        Get the original file for the given user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The path to the original file.

        Raises:
            UserProfile.DoesNotExist: If the UserProfile is not found for the given user.
            CustomSubscriptionPlan.DoesNotExist: If the CustomSubscriptionPlan is not found for the given user.
        """
        try:
            user_profile = UserProfile.objects.select_related("subscription_plan").get(
                user_id=user_id
            )
            return user_profile.subscription_plan.original_file
        except UserProfile.DoesNotExist:
            raise UserProfile.DoesNotExist("UserProfile not found for the given user.")
        except CustomSubscriptionPlan.DoesNotExist:
            raise CustomSubscriptionPlan.DoesNotExist(
                "CustomSubscriptionPlan not found for the given user."
            )

    def to_representation(self, instance):
        """
        Convert the instance to a representation.

        Args:
            instance: The instance to convert.

        Returns:
            dict: The converted representation.
        """
        data = super().to_representation(instance)
        request = self.context.get("request")

        if request:
            user_id = instance.user_id
            original_file = self.get_original_file(user_id)

            if not original_file:
                thumbnail_url = request.build_absolute_uri(
                    f"/serve-image/{instance.pk}/?q={instance.thumbnail_Basic.path}"
                )
                return {"thumbnail_Basic": thumbnail_url}
            else:
                original_url = request.build_absolute_uri(
                    f"/serve-image/{instance.pk}/?q={instance.image.path}"
                )
                thumbnail_url = request.build_absolute_uri(
                    f"/serve-image/{instance.pk}/?q={instance.thumbnail_Basic.path}"
                )
                thumbnail_premium_url = request.build_absolute_uri(
                    f"/serve-image/{instance.pk}/?q={instance.thumbnail_Premium.path}"
                )
                return {
                    "thumbnail_Basic": thumbnail_url,
                    "thumbnail_premium_url": thumbnail_premium_url,
                    "original_image": original_url,
                }

        return data


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        model = User
        fields = ["username"]
