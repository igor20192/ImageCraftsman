from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import timedelta
from django.utils import timezone


class CustomSubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    thumbnail_size = models.PositiveIntegerField()
    premium_thumbnail_size = models.PositiveIntegerField(blank=True, null=True)
    original_file = models.BooleanField(default=False)
    expiring_links = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    subscription_plan = models.ForeignKey(
        CustomSubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True
    )


class Image(models.Model):
    images = "images/"

    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to=images)
    thumbnail_Basic = models.ImageField(upload_to=images, null=True)
    thumbnail_Premium = models.ImageField(upload_to=images, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    link_expiration_time = models.PositiveIntegerField(
        default=300,
        validators=[
            MinValueValidator(
                300, "The validity of the link cannot be less than 300 seconds."
            ),
            MaxValueValidator(
                30000, "The duration of the link cannot exceed 30000 seconds."
            ),
        ],
    )
    expiration_date = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(
                seconds=self.link_expiration_time
            )
        super(Image, self).save(*args, **kwargs)
