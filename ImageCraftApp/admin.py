from django.contrib import admin
from .models import CustomSubscriptionPlan, Image, UserProfile

admin.site.register(CustomSubscriptionPlan)
admin.site.register(Image)
admin.site.register(UserProfile)
