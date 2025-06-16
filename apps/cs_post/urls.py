from django.urls import path

from . import views

urlpatterns = [
    path("", views.CSPostListCreateView.as_view(), name="cspost-list-create"),
    path("<int:pk>/", views.CSPostDetailView.as_view(), name="cspost-detail"),
]
