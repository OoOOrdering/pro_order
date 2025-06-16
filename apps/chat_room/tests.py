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
def create_user(db):
    def _create_user(email, password, is_staff=False, **kwargs):
        return User.objects.create_user(email=email, password=password, is_staff=is_staff, is_active=True, **kwargs)

    return _create_user


@pytest.fixture
def authenticate_client(api_client, create_user):
    def _authenticate_client(user=None, is_staff=False):
        if user is None:
            user = create_user(
                email=f"test_user_{timezone.now().timestamp()}@example.com",
                password="testpass123!",
                is_staff=is_staff,
            )
        login_url = reverse("user:token_login")
        response = api_client.post(login_url, {"email": user.email, "password": "testpass123!"})
        access_token = response.data["data"]["access_token"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return user

    return _authenticate_client


@pytest.fixture
def create_chat_room(db, create_user):
    def _create_chat_room(creator, participants=None, room_type=ChatRoom.RoomType.GROUP, **kwargs):
        chat_room = ChatRoom.objects.create(
            name=f"Test Chat Room {timezone.now().timestamp()}",
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
    def test_create_chat_room(self, api_client, authenticate_client, create_user):
        user1 = authenticate_client()
        user2 = create_user("user2@example.com", "testpass123!")
        url = reverse("chat_room:chat-room-list-create")
        data = {
            "name": "My New Chat Room",
            "room_type": "GROUP",
            "participant_ids": [user1.pk, user2.pk],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert ChatRoom.objects.count() == 1
        assert ChatRoomParticipant.objects.filter(chat_room=response.data["id"]).count() == 2

    def test_get_chat_room_list(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user2@example.com", "testpass123!")
        user3 = create_user("user3@example.com", "testpass123!")

        # user1이 참여하는 방
        room1 = create_chat_room(creator=user1, participants=[user2], name="Room for user1 and user2")
        # user1이 참여하지 않는 방
        room2 = create_chat_room(creator=user2, participants=[user3], name="Room for user2 and user3")

        url = reverse("chat_room:chat-room-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == room1.pk

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
        # 일반 사용자는 채팅방 이름을 변경할 수 없음
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        updated_data = {"name": "Updated Chat Room Name", "is_active": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN  # 일반 사용자는 권한 없음

        # 관리자 권한으로 변경 시도
        admin_user = authenticate_client(is_staff=True)
        ChatRoomParticipant.objects.filter(chat_room=chat_room, user=user).update(is_admin=True)
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        updated_data = {"name": "Updated Chat Room Name", "is_active": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        chat_room.refresh_from_db()
        assert chat_room.name == "Updated Chat Room Name"
        assert not chat_room.is_active

    def test_add_participants(self, api_client, authenticate_client, create_user, create_chat_room):
        admin_user = authenticate_client(is_staff=True)
        chat_room = create_chat_room(creator=admin_user)
        user3 = create_user("user3@example.com", "testpass123!")
        user4 = create_user("user4@example.com", "testpass123!")
        url = reverse("chat_room:chat-room-add-participants", kwargs={"pk": chat_room.pk})
        data = {"user_ids": [user3.pk, user4.pk]}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert (
            ChatRoomParticipant.objects.filter(chat_room=chat_room, left_at__isnull=True).count() == 3
        )  # admin + user3 + user4

    def test_remove_participants(self, api_client, authenticate_client, create_user, create_chat_room):
        admin_user = authenticate_client(is_staff=True)
        user_to_remove = create_user("user_rm@example.com", "testpass123!")
        chat_room = create_chat_room(creator=admin_user, participants=[user_to_remove])
        url = reverse("chat_room:chat-room-remove-participants", kwargs={"pk": chat_room.pk})
        data = {"user_ids": [user_to_remove.pk]}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        participant = ChatRoomParticipant.objects.get(chat_room=chat_room, user=user_to_remove)
        assert participant.left_at is not None

    def test_leave_chat_room(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_leave@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1, participants=[user2])
        authenticate_client(user=user2)  # user2로 인증
        url = reverse("chat_room:chat-room-leave", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        participant = ChatRoomParticipant.objects.get(chat_room=chat_room, user=user2)
        assert participant.left_at is not None

    def test_mark_as_read(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_read@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1, participants=[user2])
        authenticate_client(user=user2)  # user2로 인증
        url = reverse("chat_room:chat-room-mark-as-read", kwargs={"pk": chat_room.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        participant = ChatRoomParticipant.objects.get(chat_room=chat_room, user=user2)
        assert participant.last_read_at is not None

    def test_filter_chat_room_by_room_type(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_filter1@example.com", "testpass123!")
        user3 = create_user("user_filter2@example.com", "testpass123!")

        room_direct = create_chat_room(
            creator=user1,
            participants=[user2],
            room_type=ChatRoom.RoomType.DIRECT,
            name="Direct Chat",
        )
        room_group = create_chat_room(
            creator=user1,
            participants=[user3],
            room_type=ChatRoom.RoomType.GROUP,
            name="Group Chat",
        )

        url = reverse("chat_room:chat-room-list-create") + f"?room_type={ChatRoom.RoomType.DIRECT}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == room_direct.pk

    def test_filter_chat_room_by_is_active(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_filter_active1@example.com", "testpass123!")
        user3 = create_user("user_filter_active2@example.com", "testpass123!")

        room_active = create_chat_room(creator=user1, participants=[user2], is_active=True, name="Active Room")
        room_inactive = create_chat_room(creator=user1, participants=[user3], is_active=False, name="Inactive Room")

        url = reverse("chat_room:chat-room-list-create") + "?is_active=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == room_active.pk

    def test_search_chat_room_by_name(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_search1@example.com", "testpass123!")

        room_alpha = create_chat_room(creator=user1, participants=[user2], name="Alpha Chat Room")
        room_beta = create_chat_room(creator=user1, participants=[user2], name="Beta Chat Room")

        url = reverse("chat_room:chat-room-list-create") + "?search=Alpha"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == room_alpha.pk

    def test_sort_chat_room_by_created_at(self, api_client, authenticate_client, create_user, create_chat_room):
        user1 = authenticate_client()
        user2 = create_user("user_sort1@example.com", "testpass123!")

        # 두 개의 채팅방 생성, 시간차를 둠
        room_old = create_chat_room(
            creator=user1,
            participants=[user2],
            created_at=timezone.now() - timedelta(days=2),
            name="Old Room",
        )
        room_new = create_chat_room(
            creator=user1,
            participants=[user2],
            created_at=timezone.now() - timedelta(days=1),
            name="New Room",
        )

        url = reverse("chat_room:chat-room-list-create") + "?ordering=created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == room_old.pk
        assert response.data["results"][1]["id"] == room_new.pk

        url = reverse("chat_room:chat-room-list-create") + "?ordering=-created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == room_new.pk
        assert response.data["results"][1]["id"] == room_old.pk

    def test_unauthorized_access_create(self, api_client, create_user):
        user1 = create_user("unauth1@example.com", "testpass123!")
        user2 = create_user("unauth2@example.com", "testpass123!")
        url = reverse("chat_room:chat-room-list-create")
        data = {
            "name": "Unauthorized Room",
            "room_type": "GROUP",
            "participant_ids": [user1.pk, user2.pk],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # 인증되지 않은 사용자 접근

    def test_unauthorized_access_detail(self, api_client, create_user, create_chat_room):
        user1 = create_user("auth_user@example.com", "testpass123!")
        chat_room = create_chat_room(creator=user1)
        url = reverse("chat_room:chat-room-detail", kwargs={"pk": chat_room.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # 인증되지 않은 사용자 접근
