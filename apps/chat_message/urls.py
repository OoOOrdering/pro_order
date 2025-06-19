from django.urls import path

from .views import ChatMessageDetailView, ChatMessageListCreateView

app_name = "chat_message"

urlpatterns = [
    path(
        "<int:chat_room_pk>/messages/",
        ChatMessageListCreateView.as_view(),
        name="chat-message-list-create",
    ),
    path(
        "<int:chat_room_pk>/messages/<int:pk>/",
        ChatMessageDetailView.as_view(),
        name="chat-message-detail",
    ),
]
