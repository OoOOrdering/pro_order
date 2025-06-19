from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.chat_room.models import ChatRoom, ChatRoomParticipant
from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate_client(api_client):
    def _authenticate_client(user=None, is_staff=False):
        if user is None:
            timestamp = timezone.now().timestamp()
            user = User.objects.create_user(
                email=f"test_user_{timestamp}@example.com",
                password="testpass123!",
                nickname=f"test_user_{timestamp}",
                is_staff=is_staff,
                is_active=True,
            )
        api_client.force_authenticate(user=user)
        return user

    return _authenticate_client


@pytest.fixture
def create_chat_room(db, create_user):
    def _create_chat_room(creator, participants=None, room_type=ChatRoom.RoomType.GROUP, **kwargs):
        timestamp = timezone.now().timestamp()
        chat_room = ChatRoom.objects.create(
            name=kwargs.pop("name", f"Test Chat Room {timestamp}"),
            room_type=room_type,
            created_by=creator,
            **kwargs,
        )
        ChatRoomParticipant.objects.create(chat_room=chat_room, user=creator, is_admin=True, joined_at=timezone.now())
        if participants:
            for participant_user in participants:
                if participant_user != creator:
                    ChatRoomParticipant.objects.create(
                        chat_room=chat_room,
                        user=participant_user,
                        joined_at=timezone.now(),
                    )
        return chat_room

    return _create_chat_room


@pytest.mark.django_db
class TestChatRoomAPI:
    @pytest.fixture
    def chat_room_data(self):
        return {
            "name": "Test Chat Room",
            "max_participants": 5,
            "description": "Test Description",
            "participant_ids": [],
        }

    def test_list_chat_rooms(self, api_client, authenticate_client, chat_room):
        authenticate_client()
        url = reverse("chat_room:chat-room-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_chat_room(self, api_client, authenticate_client, chat_room):
        authenticate_client()
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_update_chat_room_by_creator(self, api_client, authenticate_client, chat_room):
        authenticate_client(user=chat_room.created_by)  # chat_room의 생성자로 인증
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.patch(url, {"name": "Updated Room"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_update_chat_room_by_non_creator(self, api_client, authenticate_client, chat_room, another_user):
        authenticate_client(user=another_user)
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.patch(url, {"name": "Updated Room"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_chat_room_by_creator(self, api_client, authenticate_client, chat_room):
        authenticate_client(user=chat_room.created_by)  # chat_room의 생성자로 인증
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_chat_room_by_non_creator(self, api_client, authenticate_client, chat_room, another_user):
        authenticate_client(user=another_user)
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_join_chat_room(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user2@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1)

        api_client.force_authenticate(user=user2)
        url = reverse("chat_room:chat-room-join", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert ChatRoomParticipant.objects.filter(chat_room=chat_room, user=user2).exists()

    def test_join_full_chat_room(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user2@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1, max_participants=1)

        api_client.force_authenticate(user=user2)
        url = reverse("chat_room:chat-room-join", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_leave_chat_room(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_leave@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1, participants=[user2])

        api_client.force_authenticate(user=user2)
        url = reverse("chat_room:chat-room-leave", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        participant = ChatRoomParticipant.objects.get(chat_room=chat_room, user=user2)
        assert participant.left_at is not None

    def test_leave_chat_room_not_participant(self, api_client, authenticate_client, chat_room, another_user):
        api_client.force_authenticate(user=another_user)
        url = reverse("chat_room:chat-room-leave", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_creator_cannot_leave_chat_room(self, api_client, authenticate_client, chat_room):
        authenticate_client(user=chat_room.created_by)  # chat_room의 생성자로 인증
        url = reverse("chat_room:chat-room-leave", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_chat_room_list(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user2@example.com", "testpass123!")
        user3 = create_user("user3@example.com", "testpass123!")

        room1 = create_chat_room(creator=user1, participants=[user2])
        room2 = create_chat_room(creator=user2, participants=[user3])

        url = reverse("chat_room:chat-room-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1  # user1이 참여 중인 채팅방만 보여야 함
        assert len(response.data["results"]) == 1

    def test_get_chat_room_detail(self, api_client, authenticate_client, create_chat_room):
        user = authenticate_client()
        chat_room = create_chat_room(creator=user)

        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == chat_room.name

    def test_update_chat_room(self, api_client, authenticate_client, create_chat_room):
        user = authenticate_client()
        chat_room = create_chat_room(creator=user, room_type=ChatRoom.RoomType.GROUP)

        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        updated_data = {"name": "Updated Chat Room Name", "is_active": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_add_participants(self, api_client, authenticate_client, create_user, create_chat_room):
        admin_user = authenticate_client(is_staff=True)
        chat_room = create_chat_room(creator=admin_user)
        user3 = create_user("user3@example.com", "testpass123!")
        user4 = create_user("user4@example.com", "testpass123!")

        url = reverse("chat_room:chat-room-add-participants", kwargs={"pk": chat_room.pk})
        data = {"user_ids": [user3.pk, user4.pk]}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_remove_participants(self, api_client, authenticate_client, create_user, create_chat_room):
        admin_user = authenticate_client(is_staff=True)
        user_to_remove = create_user("user_rm@example.com", "testpass123!")
        chat_room = create_chat_room(creator=admin_user, participants=[user_to_remove])

        url = reverse("chat_room:chat-room-remove-participants", kwargs={"pk": chat_room.pk})
        data = {"user_ids": [user_to_remove.pk]}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_mark_as_read(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_read@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1, participants=[user2])

        api_client.force_authenticate(user=user2)
        url = reverse("chat_room:chat-room-mark-as-read", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_filter_chat_room_by_room_type(self, api_client, authenticate_client, create_chat_room):
        user1 = authenticate_client()
        room_direct = create_chat_room(creator=user1, room_type=ChatRoom.RoomType.DIRECT, name="Direct Chat")
        room_group = create_chat_room(creator=user1, room_type=ChatRoom.RoomType.GROUP, name="Group Chat")

        url = reverse("chat_room:chat-room-list-create") + f"?room_type={ChatRoom.RoomType.DIRECT}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["room_type"] == ChatRoom.RoomType.DIRECT

    def test_filter_chat_room_by_is_active(self, api_client, authenticate_client, create_chat_room):
        user1 = authenticate_client()
        room_active = create_chat_room(creator=user1, is_active=True, name="Active Room")
        room_inactive = create_chat_room(creator=user1, is_active=False, name="Inactive Room")

        url = reverse("chat_room:chat-room-list-create") + "?is_active=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["is_active"] == True

    def test_search_chat_room_by_name(self, api_client, authenticate_client, create_chat_room):
        user1 = authenticate_client()
        room_alpha = create_chat_room(creator=user1, name="Alpha Chat Room")
        room_beta = create_chat_room(creator=user1, name="Beta Chat Room")

        url = reverse("chat_room:chat-room-list-create") + "?search=Alpha"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert "Alpha" in response.data["results"][0]["name"]

    def test_sort_chat_room_by_created_at(self, api_client, authenticate_client, create_chat_room):
        user1 = authenticate_client()
        room_old = create_chat_room(creator=user1, name="Old Room", created_at=timezone.now() - timedelta(days=2))
        room_new = create_chat_room(creator=user1, name="New Room", created_at=timezone.now() - timedelta(days=1))

        url = reverse("chat_room:chat-room-list-create") + "?ordering=created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["name"] == "Old Room"
        assert response.data["results"][1]["name"] == "New Room"

    def test_unauthorized_access_create(self, api_client, create_user):
        user1 = create_user("unauth1@example.com", "testpass123!")
        user2 = create_user("unauth2@example.com", "testpass123!")

        url = reverse("chat_room:chat-room-list-create")
        data = {
            "name": "New Chat Room",
            "max_participants": 5,
            "description": "Test Description",
            "participant_ids": [user2.pk],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthorized_access_detail(self, api_client, create_user, create_chat_room):
        user = create_user("unauth_detail@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user)

        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
