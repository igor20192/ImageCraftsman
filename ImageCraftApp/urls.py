from django.urls import path
from .views import ImageCreateView, UserDetailView, ImageDetailView, ServeImageView

urlpatterns = [
    path("upload/", ImageCreateView.as_view(), name="upload-image"),
    path("user/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("image_detail/<int:pk>/", ImageDetailView.as_view(), name="image-detail"),
    path("serve-image/<int:pk>/", ServeImageView.as_view(), name="serve_image"),
]
