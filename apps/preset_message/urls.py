from django.urls import path

from .views import PresetMessageDetailView, PresetMessageListCreateView

app_name = "preset_message"

urlpatterns = [
    path(
        "",
        PresetMessageListCreateView.as_view(),
        name="preset-message-list-create",
    ),
    path(
        "<int:pk>/",
        PresetMessageDetailView.as_view(),
        name="preset-message-detail",
    ),
]
