from rest_framework import serializers
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Image, UserProfile


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ["title", "image", "link_expiration_time"]

    def to_representation(self, instance):
        original_file = get_object_or_404(
            UserProfile, user=instance.user_id
        ).subscription_plan.original_file

        data = super().to_representation(instance)

        if self.context.get("create_mode", False):
            return data

        request = self.context.get("request")

        if request:
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


class ImageSerializerBasic(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ["thumbnail_Basic"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["username"]
