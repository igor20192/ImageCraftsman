from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Image


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ["title", "image", "link_expiration_time"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get("create_mode", False):
            return data

        request = self.context.get("request")
        subscription_plan = self.context.get("subscription_plan")

        if request:
            if subscription_plan == "Basic":
                thumbnail_url = request.build_absolute_uri(instance.thumbnail_Basic.url)
                return {"thumbnail_Basic": thumbnail_url}
            else:
                original_url = request.build_absolute_uri(instance.image.url)
                thumbnail_url = request.build_absolute_uri(instance.thumbnail_Basic.url)
                thumbnail_premium_url = request.build_absolute_uri(
                    instance.thumbnail_Premium.url
                )
                return {
                    "thumbnail_Basic": thumbnail_url,
                    "thumbnail_premium_url": thumbnail_premium_url,
                    "original_url": original_url,
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