import os
from django.shortcuts import render
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Image, UserProfile
from .serializers import (
    ImageSerializer,
    ImageSerializerBasic,
    UserSerializer,
)


class ImageCreateView(generics.CreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    @staticmethod
    def create_image(instance, size):
        image = PILImage.open(instance.image.path)
        image.thumbnail((size, size))
        thumbnail_io = BytesIO()
        image.save(thumbnail_io, "JPEG")
        thumbnail_io.seek(0)
        thumbnail_name = os.path.join(
            f"images_{size}", f"{instance.pk}_thumbnail_{size}.jpeg"
        )
        thumbnail_file = SimpleUploadedFile(
            thumbnail_name, thumbnail_io.read(), content_type="image/jpeg"
        )
        instance.thumbnail_Basic.save(thumbnail_name, thumbnail_file, save=False)
        instance.save()

    def perform_create(self, serializer):
        user = self.request.user
        userprofile = get_object_or_404(UserProfile, user=user)
        subscription_plan = userprofile.subscription_plan.name
        thumbnail_size = userprofile.subscription_plan.thumbnail_size
        premium_thumbnail_size = userprofile.subscription_plan.premium_thumbnail_size
        instance = serializer.save(user=user)
        self.create_image(instance, thumbnail_size)

        # if subscription_plan in (
        # "Premium",
        # "Enterprise",
        # ):
        # self.create_image(instance, premium_thumbnail_size)

        context = (
            {"create_mode": True}
            | {"request": self.request}
            | {"subscription_plan": subscription_plan}
        )
        response_serializer = ImageSerializer(instance, context=context)
        data = response_serializer.data

        # Return the customized response
        return Response(data)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class ImageDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        subscription_plan = get_object_or_404(
            UserProfile, user=user
        ).subscription_plan.name
        if subscription_plan == "Basic":
            return ImageSerializerBasic
        return ImageSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Image.objects.filter(user=user)
        return queryset
