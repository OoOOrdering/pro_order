# # tests/image/test_views.py
#
# import io
#
# import pytest
# from django.contrib.auth import get_user_model
# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.urls import reverse
# from PIL import Image as PilImage
# from rest_framework import status
# from rest_framework.test import APIClient
#
# User = get_user_model()
#
#
# @pytest.fixture
# def user(db):
#     return User.objects.create_user(email="test@example.com", password="password123")
#
#
# @pytest.fixture
# def auth_client(user):
#     client = APIClient()
#     response = client.post(
#         "/api/auth/login/",
#         {"email": user.email, "password": "password123"},
#         format="json",
#     )
#     token = response.data["data"]["access_token"]
#     client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
#     return client
#
#
# def generate_image_file(name="test.jpg"):
#     file = io.BytesIO()
#     image = PilImage.new("RGB", (100, 100), color="blue")
#     image.save(file, "JPEG")
#     file.name = name
#     file.seek(0)
#     return SimpleUploadedFile(name, file.read(), content_type="image/jpeg")
#
#
# def test_image_upload(auth_client, create_user):
#     user = create_user(email="testimg@example.com", password="1234")
#     url = reverse("image:upload")
#     image_file = generate_image_file()
#
#     data = {
#         "image": image_file,
#         "object_type": "user",
#         "object_id": str(user.id),  # 반드시 문자열로
#     }
#
#     response = auth_client.post(url, data, format="multipart")
#
#     print("STATUS:", response.status_code)
#     print("RESPONSE:", response.data)
#
#     assert response.status_code == 201
#     assert isinstance(response.data["data"], list)
#     assert "image_url" in response.data["data"][0]
#     assert "public_id" in response.data["data"][0]
#
#
# def test_image_delete(auth_client):
#     url = reverse("image:upload")
#     image_file = generate_image_file()
#
#     # 먼저 업로드
#     upload_data = {
#         "object_type": "user",
#         "object_id": 1,
#         "image": image_file,
#     }
#     upload_response = auth_client.post(url, upload_data, format="multipart")
#     assert upload_response.status_code == 201
#
#     public_id = upload_response.data["data"][0]["public_id"]
#
#     # 삭제 요청
#     delete_data = {
#         "object_type": "user",
#         "object_id": 1,
#         "public_id": public_id,
#     }
#     response = auth_client.delete(url, data=delete_data, format="multipart")
#     assert response.status_code == status.HTTP_200_OK
#     assert response.data["data"]["deleted"] is True
