from django.urls import path

from . import views

app_name = "cs_post"

urlpatterns = [
    path("", views.CSPostListCreateView.as_view(), name="cspost-list-create"),
    path("<int:pk>/", views.CSPostDetailView.as_view(), name="cspost-detail"),
]
