from django.urls import path

from .views import PresetMessageDetailView, PresetMessageListCreateView

urlpatterns = [
    path(
        "preset-messages/",
        PresetMessageListCreateView.as_view(),
        name="preset-message-list-create",
    ),
    path(
        "preset-messages/<int:pk>/",
        PresetMessageDetailView.as_view(),
        name="preset-message-detail",
    ),
]
