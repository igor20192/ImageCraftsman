from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from .models import Image
from .models import (
    UserProfile,
    CustomSubscriptionPlan,
)  # Assuming you have UserProfile model
from .serializers import ImageSerializer  # Import your serializer


class ImageCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.client.force_authenticate(user=self.user)

        # Create a CustomSubscriptionPlan instance
        self.subscription_plan = CustomSubscriptionPlan.objects.create(
            name="Basic", thumbnail_size=200
        )

        # Create a UserProfile for the authenticated user (adjust as needed)
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            subscription_plan=self.subscription_plan,  # Adjust based on your subscription plans
        )

        # Read the image file and encode it to base64
        with open("ImageCraftApp/media/images/Котя.jpg", "rb") as image_file:
            image_data = image_file.read()

        # Define test data for creating an image
        self.image_data = {
            "title": "Koty",
            "image": SimpleUploadedFile(
                "Котя.jpg", image_data, content_type="image/jpeg"
            ),  # Replace with actual image data
        }

        with open("ImageCraftApp/media/images/Котя.jpg", "rb") as image_file:
            self.image_file = SimpleUploadedFile(
                name="Котя.jpg", content=image_file.read(), content_type="image/jpeg"
            )
        self.image = Image.objects.create(
            title="Test Image",
            image=self.image_file,  # Set the image
            user=self.user,
        )

    def test_create_image_with_thumbnail(self):
        response = self.client.post("/upload/", self.image_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the image object is created
        self.assertTrue(Image.objects.filter(title="Koty").exists())

        # Check if the thumbnail_Basic field is populated
        created_image = Image.objects.get(title="Koty")
        self.assertIsNotNone(created_image.thumbnail_Basic)

        # You can add more assertions as needed based on your view's functionality

    def test_create_image_without_thumbnail(self):
        # Modify the user's subscription plan to one without premium thumbnails
        self.user_profile.subscription_plan = self.subscription_plan
        self.user_profile.save()

        response = self.client.post("/upload/", self.image_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the image object is created
        self.assertTrue(Image.objects.filter(title="Koty").exists())

        # Check if the thumbnail_Basic field is populated
        created_image = Image.objects.get(title="Koty")
        self.assertIsNotNone(created_image.thumbnail_Basic)

        # Check if the thumbnail_Premium field is None
        self.assertIsNone(created_image.thumbnail_Premium._file)

        # You can add more assertions as needed based on your view's functionality

    def test_serve_image_with_valid_link(self):
        # Authenticate the user
        self.client.force_authenticate(self.user)

        # Construct the URL for serving the image
        url = f"/serve-image/{self.image.pk}/?q={self.image.image.path}"

        # Send a GET request to serve the image
        response = self.client.get(url)

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the response content type is 'image/jpeg' (or the appropriate content type)
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test_serve_image_with_expired_link(self):
        # Authenticate the user
        self.client.force_authenticate(self.user)

        # Set the expiration date of the image to a past date to simulate an expired link
        self.image.expiration_date = timezone.now() - timezone.timedelta(hours=1)
        self.image.save()

        # Construct the URL for serving the image
        url = f"/serve-image/{self.image.pk}/?q={self.image.image.path}"

        # Send a GET request to serve the image
        response = self.client.get(url)

        # Assert that the response status code is 403 (Forbidden) for an expired link
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_serve_nonexistent_image(self):
        # Authenticate the user
        self.client.force_authenticate(self.user)

        # Construct the URL for serving a nonexistent image
        url = f"/serve-image/{self.image.pk}/?q=nonexistent_path.jpg"

        # Send a GET request to serve the nonexistent image
        response = self.client.get(url)

        # Assert that the response status code is 404 (Not Found) for a nonexistent image
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
