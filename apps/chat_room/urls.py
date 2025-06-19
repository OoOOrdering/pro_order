from django.urls import path

from .views import (
    ChatRoomDetailView,
    ChatRoomJoinView,
    ChatRoomLeaveView,
    ChatRoomListCreateView,
    ChatRoomMarkAsReadView,
    ChatRoomParticipantAddView,
    ChatRoomParticipantRemoveView,
)

app_name = "chat_room"

urlpatterns = [
    path("chat-rooms/", ChatRoomListCreateView.as_view(), name="chat-room-list-create"),
    path("chat-rooms/<int:pk>/", ChatRoomDetailView.as_view(), name="chat-room-detail"),
    path(
        "chat-rooms/<int:pk>/add-participants/",
        ChatRoomParticipantAddView.as_view(),
        name="chat-room-add-participants",
    ),
    path(
        "chat-rooms/<int:pk>/remove-participants/",
        ChatRoomParticipantRemoveView.as_view(),
        name="chat-room-remove-participants",
    ),
    path(
        "chat-rooms/<int:pk>/leave/",
        ChatRoomLeaveView.as_view(),
        name="chat-room-leave",
    ),
    path(
        "chat-rooms/<int:pk>/mark-as-read/",
        ChatRoomMarkAsReadView.as_view(),
        name="chat-room-mark-as-read",
    ),
    path(
        "chat-rooms/<int:pk>/join/",
        ChatRoomJoinView.as_view(),
        name="chat-room-join",
    ),
]
