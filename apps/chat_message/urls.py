from django.urls import path

from .views import ChatMessageDetailView, ChatMessageListCreateView

urlpatterns = [
    path(
        "chat-rooms/<int:chat_room_pk>/messages/",
        ChatMessageListCreateView.as_view(),
        name="chat-message-list-create",
    ),
    path(
        "chat-rooms/<int:chat_room_pk>/messages/<int:pk>/",
        ChatMessageDetailView.as_view(),
        name="chat-message-detail",
    ),
]
