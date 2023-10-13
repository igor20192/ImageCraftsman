from django.http import HttpResponseNotFound
from django.utils import timezone
import os
from django.shortcuts import render, HttpResponse
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from asgiref.sync import sync_to_async, async_to_sync
from .models import Image, UserProfile, CustomSubscriptionPlan
from .serializers import (
    ImageSerializer,
    ImageSerializerBasic,
    UserSerializer,
)


@method_decorator(cache_page(60 * 15), name="post")
class ImageCreateView(generics.CreateAPIView):
    """
    A view for creating image objects and generating thumbnails.

    This view allows authenticated users to create image objects and automatically generate thumbnails based on the uploaded image.
    The generated thumbnails are saved in the corresponding fields of the image object.

    Attributes:
        queryset (QuerySet): The queryset of all images.
        serializer_class (class): The serializer class for this view.
        permission_classes (list): The list of permission classes required for accessing this view.
    """

    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    async def create_thumbnail(self, instance, size):
        """
        Create a thumbnail for the given image instance.

        This method opens the image file, resizes it to the specified size, and saves the thumbnail as a JPEG image.
        The thumbnail is returned as an in-memory file-like object.

        Args:
            instance (Image): The image instance for which to create the thumbnail.
            size (int): The size (in pixels) of the thumbnail.

        Returns:
            BytesIO: The in-memory file-like object containing the thumbnail image.
        """
        image = PILImage.open(instance.image.path)
        image.thumbnail((size, size))
        thumbnail_io = BytesIO()
        image.save(thumbnail_io, "JPEG")
        thumbnail_io.seek(0)
        return thumbnail_io

    async def save_thumbnail(
        self, instance, thumbnail_name, thumbnail_io, subscription_plan=None
    ):
        """
        Save a thumbnail for the given image instance.

        Args:
            instance (Image): The image instance for which to save the thumbnail.
            thumbnail_name (str): The name of the thumbnail file.
            thumbnail_io (BytesIO): The in-memory file-like object containing the thumbnail image.
        """
        thumbnail_file = SimpleUploadedFile(
            thumbnail_name, thumbnail_io.read(), content_type="image/jpeg"
        )
        if subscription_plan:
            instance.thumbnail_Premium.save(thumbnail_name, thumbnail_file, save=False)
        else:
            instance.thumbnail_Basic.save(thumbnail_name, thumbnail_file, save=False)

    async def create_thumbnails(
        self, instance, subscription_plan, thumbnail_size, premium_thumbnail_size
    ):
        thumbnail_io = await self.create_thumbnail(instance, thumbnail_size)
        thumbnail_name = os.path.join(
            f"thumbnail_{thumbnail_size}.jpeg",
        )
        await self.save_thumbnail(instance, thumbnail_name, thumbnail_io)
        if subscription_plan in ("Premium", "Enterprise"):
            thumbnail_io = await self.create_thumbnail(instance, premium_thumbnail_size)
            thumbnail_name = os.path.join(
                f"thumbnail_{premium_thumbnail_size}.jpeg",
            )
            await self.save_thumbnail(
                instance, thumbnail_name, thumbnail_io, subscription_plan
            )

        await sync_to_async(instance.save)()

    def serealizer_data(self, instance):
        response_serializer = ImageSerializer(instance, context={"create_mode": True})
        data = response_serializer.data
        return Response(data)

    @async_to_sync
    async def perform_create(self, serializer):
        user = self.request.user
        user_profile = await sync_to_async(get_object_or_404)(UserProfile, user=user)
        subscription_plan = await sync_to_async(get_object_or_404)(
            CustomSubscriptionPlan, pk=user_profile.subscription_plan_id
        )
        thumbnail_size = subscription_plan.thumbnail_size
        premium_thumbnail_size = subscription_plan.premium_thumbnail_size
        instance = await sync_to_async(serializer.save)(user=user)
        await self.create_thumbnails(
            instance, subscription_plan.name, thumbnail_size, premium_thumbnail_size
        )
        await sync_to_async(self.serealizer_data)(instance)


class ServeImageView(generics.RetrieveAPIView):
    """
    A view for serving image files based on the provided path.

    This view retrieves and serves image files based on the given path parameter.
    It requires authentication for accessing the view and handles cases where the link has expired or the file does not exist.

    Attributes:
        serializer_class (class): The serializer class for this view.
        permission_classes (list): The list of permission classes required for accessing this view.
    """

    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the queryset of images based on the user.

        Returns:
            queryset: The queryset of images based on the user's role.
        """
        user = self.request.user
        if user.is_staff:
            return Image.objects.all()
        queryset = Image.objects.filter(user=user)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve and serve the image file.

        This method retrieves the image object based on the provided parameters.
        It checks if the link has expired and if the file exists.
        If the link has expired, it returns a 403 Forbidden response.
        If the file exists, it opens the file and returns the file content as an HTTP response.
        If the file does not exist, it returns a response indicating the file is not found.

        Returns:
            HttpResponse or Response: The HTTP response with the image content or an error response.
        """
        instance = self.get_object()
        user = self.request.user
        expiring_links = get_object_or_404(
            UserProfile, user=user
        ).subscription_plan.expiring_links
        if instance.expiration_date < timezone.now() and expiring_links is not True:
            return Response({"detail": "This link has expired."}, status=403)

        path = self.request.GET.get("q")
        if path:
            try:
                with open(path, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/jpeg")
            except FileNotFoundError:
                return HttpResponseNotFound("The requested file does not exist.")
        Response(
            {
                "detail": "The file you are linking to does not exist. Please check the file path is correct and make sure the file actually exists"
            }
        )


class UserDetailView(generics.RetrieveAPIView):
    """
    A view to retrieve user details.
    You should provide more details about the user detail view or the specific functionality it serves.
    """

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
