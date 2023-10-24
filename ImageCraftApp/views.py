from django.http import HttpResponseNotFound
from django.utils import timezone
import os
from django.shortcuts import render, HttpResponse
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import NotFound
from asgiref.sync import sync_to_async, async_to_sync
from .models import Image, UserProfile, CustomSubscriptionPlan
from .serializers import (
    ImageSerializer,
    UserSerializer,
)


class ImageCreateView(generics.CreateAPIView):
    """
    A view for creating an image with thumbnails.
    """

    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    async def create_thumbnail(self, instance, size):
        """
        Create a thumbnail image with the given size.

        Args:
            instance (Image): The image instance.
            size (int): The size of the thumbnail.

        Returns:
            BytesIO: The thumbnail image as BytesIO object.
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
        Save the thumbnail image.

        Args:
            instance (Image): The image instance.
            thumbnail_name (str): The name of the thumbnail image.
            thumbnail_io (BytesIO): The thumbnail image as BytesIO object.
            subscription_plan (str, optional): The subscription plan. Defaults to None.
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
        """
        Create thumbnails for the image.

        Args:
            instance (Image): The image instance.
            subscription_plan (str): The subscription plan.
            thumbnail_size (int): The size of the basic thumbnail.
            premium_thumbnail_size (int): The size of the premium thumbnail.
        """
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

    @sync_to_async
    def serealizer_data(self, instance):
        """
        Get serialized data for the image instance.

        Args:
            instance (Image): The image instance.

        Returns:
            Response: The serialized data as a Response object.
        """
        response_serializer = ImageSerializer(instance)
        data = response_serializer.data
        return Response(data)

    async def get_user_profile(self, user):
        """
        Get the user profile for the given user.

        Args:
            user (User): The user.

        Returns:
            UserProfile: The user profile.

        Raises:
            ObjectDoesNotExist: If the user profile is not found.
        """
        try:
            return await UserProfile.objects.select_related(
                "user", "subscription_plan"
            ).aget(user=user)
        except ObjectDoesNotExist:
            message = "UserProfile not found for the given user."
            raise ObjectDoesNotExist(message)

    async def get_subscription_plan(self, plan_id):
        """
        Get the subscription plan for the given plan ID.

        Args:
            plan_id (int): The plan ID.

        Returns:
            CustomSubscriptionPlan: The subscription plan.

        Raises:
            ObjectDoesNotExist: If the subscription plan is not found.
        """
        cache_key = f"subscription_plan_{plan_id}"
        cached_plan = cache.get(cache_key)

        if cached_plan is not None:
            return cached_plan

        try:
            plan = await CustomSubscriptionPlan.objects.aget(pk=plan_id)
            cache.set(cache_key, plan)  # Cache the result
            return plan
        except Exception:  # CustomSubscriptionPlan.DoesNotExist:
            raise ObjectDoesNotExist(
                "CustomSubscriptionPlan not found for the given plan_id."
            )

    @async_to_sync
    async def perform_create(self, serializer):
        """
        Perform the creation of the image.

        Args:
            serializer (ImageSerializer): The image serializer.
        """
        user = self.request.user
        user_profile = await self.get_user_profile(user)
        subscription_plan = await self.get_subscription_plan(
            user_profile.subscription_plan_id
        )
        thumbnail_size = subscription_plan.thumbnail_size
        premium_thumbnail_size = subscription_plan.premium_thumbnail_size
        instance = await sync_to_async(serializer.save)(user=user)
        await self.create_thumbnails(
            instance,
            subscription_plan.name,
            thumbnail_size,
            premium_thumbnail_size,
        )
        await self.serealizer_data(instance)


class ServeImageView(generics.RetrieveAPIView):
    """
    A view for serving images with expiring links.

    This view allows authenticated users to access images with expiring links.
    If the link is still valid, the image is served; otherwise, an error response is returned.

    Attributes:
        serializer_class (class): The serializer class for this view.
        permission_classes (list): The list of permission classes required for accessing this view.
    """

    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the queryset of images based on the user's permissions.

        Returns:
            QuerySet: The queryset of images to serve.
        """
        user = self.request.user
        if user.is_staff:
            return Image.objects.all()
        return Image.objects.filter(user=user)

    def get_user_profile(self, user):
        """
        Get the user's profile, including the related subscription plan.

        This function retrieves the user's profile from the database, including the related subscription plan.

        Args:
            user (User): The user for whom to retrieve the profile.

        Returns:
            UserProfile: The user's profile with subscription plan.

        Raises:
            NotFound: If the user's profile is not found in the database.
        """
        try:
            return UserProfile.objects.select_related("subscription_plan").get(
                user=user
            )
        except UserProfile.DoesNotExist:
            raise NotFound("UserProfile not found for the given user.")

    def open_image(self, path):
        """
        Open and serve the image at the specified path.

        Args:
            path (str): The file path to the image.

        Returns:
            HttpResponse: The HTTP response with the image content.

        Raises:
            NotFound: If the requested file does not exist.
        """
        try:
            with open(path, "rb") as f:
                return HttpResponse(f.read(), content_type="image/jpeg")
        except FileNotFoundError:
            raise NotFound("The requested file does not exist.")

    def retrieve(self, request, *args, **kwargs):
        """
        Serve the image with expiring link functionality.

        If the link is still valid, serve the image; otherwise, return an error response.

        Args:
            request: The HTTP request.
            args: Additional positional arguments.
            kwargs: Additional keyword arguments.

        Raises:
            PermissionDenied: If the link has expired.
            NotFound: If the requested file does not exist.
        """
        instance = self.get_object()
        user = self.request.user
        expiring_links = self.get_user_profile(user).subscription_plan.expiring_links

        if (
            instance.expiration_date < timezone.now()
            and not expiring_links
            and not user.is_staff
        ):
            return Response({"detail": "This link has expired."}, status=403)

        path = self.request.GET.get("q")
        if path:
            return self.open_image(path)
        raise NotFound(
            "The file you are linking to does not exist. Please check the file path is correct."
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
    """
    Retrieve detailed information about an image.

    This view allows authenticated users to retrieve detailed information about a specific image.
    The information includes details about the image, such as title and thumbnail URLs.

    Attributes:
        serializer_class (class): The serializer class for this view.
        permission_classes (list): The list of permission classes required for accessing this view.

    Methods:
        get_queryset(self): Get the queryset of images based on the user's role.

    Attributes:
        queryset (QuerySet): The queryset of images for the view.

    Returns:
        Response: A serialized response with detailed information about the image.

    Permission:
        The user must be authenticated to access this view.
    """

    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the queryset of images based on the user's role.

        If the user is a staff member, return all images. Otherwise, return images associated
        with the user.

        Returns:
            QuerySet: The queryset of images.
        """
        user = self.request.user

        if user.is_staff:
            return Image.objects.all()
        return Image.objects.filter(user=user)
