import io
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.chat_message.models import ChatMessage
from apps.chat_room.models import ChatRoom


@pytest.fixture
def chat_room(db, create_user):
    user = create_user(nickname="chatroom_creator")
    return ChatRoom.objects.create(name="Test Chat Room", created_by=user)


@pytest.fixture
def image_file():
    # Create a test image file
    file = io.BytesIO()
    image = Image.new("RGB", (100, 100), "white")
    image.save(file, "PNG")
    file.seek(0)
    return SimpleUploadedFile("test.png", file.getvalue(), content_type="image/png")


@pytest.mark.django_db
class TestChatMessageAPI:
    def test_create_text_message(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser1")
        api_client.force_authenticate(user=user)
        data = {"chat_room": chat_room.id, "message_type": "text", "content": "Hello, world!"}

        response = api_client.post(f"/chat-rooms/{chat_room.id}/messages/", data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["content"] == "Hello, world!"
        assert response.data["data"]["sender"]["id"] == user.id
        assert not response.data["data"]["is_read"]

    def test_create_text_message_without_content(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser2")
        api_client.force_authenticate(user=user)
        data = {
            "chat_room": chat_room.id,
            "message_type": "text",
        }

        response = api_client.post(f"/chat-rooms/{chat_room.id}/messages/", data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_image_message(self, api_client: APIClient, create_user, chat_room, image_file):
        user = create_user(nickname="imguser1")
        api_client.force_authenticate(user=user)
        data = {"chat_room": chat_room.id, "message_type": "image", "image": image_file}

        response = api_client.post(f"/chat-rooms/{chat_room.id}/messages/", data=data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["message_type"] == "image"
        assert response.data["data"]["image"] is not None

    def test_list_messages(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser3")
        api_client.force_authenticate(user=user)
        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=user, message_type="text", content="Test message"
        )
        response = api_client.get(f"/chat-rooms/{chat_room.id}/messages/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]["content"] == text_message.content

    def test_update_message_within_time_limit(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser4")
        api_client.force_authenticate(user=user)
        # 메시지를 user가 sender로 생성
        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=user, message_type="text", content="Test message"
        )
        data = {"content": "Updated message"}

        response = api_client.patch(
            f"/chat-rooms/{text_message.chat_room.id}/messages/{text_message.id}/", data=data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["content"] == "Updated message"

    def test_update_message_after_time_limit(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser5")
        api_client.force_authenticate(user=user)
        from django.utils import timezone

        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=user, message_type="text", content="Test message"
        )
        text_message.timestamp = timezone.now() - timedelta(minutes=6)
        text_message.save()
        data = {"content": "Updated message"}
        response = api_client.patch(
            f"/chat-rooms/{text_message.chat_room.id}/messages/{text_message.id}/", data=data, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_message_within_time_limit(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser6")
        api_client.force_authenticate(user=user)
        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=user, message_type="text", content="Test message"
        )

        response = api_client.delete(f"/chat-rooms/{text_message.chat_room.id}/messages/{text_message.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ChatMessage.objects.filter(id=text_message.id).exists()

    def test_delete_message_after_time_limit(self, api_client: APIClient, create_user, chat_room):
        user = create_user(nickname="msguser7")
        api_client.force_authenticate(user=user)
        from django.utils import timezone

        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=user, message_type="text", content="Test message"
        )
        text_message.timestamp = timezone.now() - timedelta(minutes=6)
        text_message.save()
        response = api_client.delete(f"/chat-rooms/{text_message.chat_room.id}/messages/{text_message.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ChatMessage.objects.filter(id=text_message.id).exists()

    def test_other_user_cannot_update_message(self, api_client: APIClient, create_user, chat_room):
        sender = create_user(nickname="msguser8")
        another_user = create_user(nickname="otheruser1")
        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=sender, message_type="text", content="Test message"
        )
        api_client.force_authenticate(user=another_user)
        data = {"content": "Updated by another user"}
        response = api_client.patch(
            f"/chat-rooms/{text_message.chat_room.id}/messages/{text_message.id}/", data=data, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_other_user_cannot_delete_message(self, api_client: APIClient, create_user, chat_room):
        sender = create_user(nickname="msguser9")
        another_user = create_user(nickname="otheruser2")
        from apps.chat_message.models import ChatMessage

        text_message = ChatMessage.objects.create(
            chat_room=chat_room, sender=sender, message_type="text", content="Test message"
        )
        api_client.force_authenticate(user=another_user)
        response = api_client.delete(f"/chat-rooms/{text_message.chat_room.id}/messages/{text_message.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ChatMessage.objects.filter(id=text_message.id).exists()
