from django.urls import path

from .views import ImageUploadView

app_name = "image"

urlpatterns = [
    path("upload", ImageUploadView.as_view(), name="upload"),
]
