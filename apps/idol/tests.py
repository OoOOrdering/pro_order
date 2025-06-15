# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase
# from rest_framework_simplejwt.tokens import RefreshToken
#
# from apps.idol.models import Idol
# from apps.user.models import User
#
#
# class TestIdolAPI(APITestCase):
#     def setUp(self):
#         # 테스트 유저 생성
#         self.user = User.objects.create_user(
#             email="test@example.com",
#             password="password123",
#             nickname="testuser",
#             name="테스트",
#             is_active=True,
#         )
#         # JWT 토큰 생성
#         refresh = RefreshToken.for_user(self.user)
#         self.access_token = str(refresh.access_token)
#
#         # 테스트 아이돌 생성
#         self.idol = Idol.objects.create(
#             name="테스트아이돌",
#             debut_date="2020-01-01",
#             agency="테스트엔터",
#             description="테스트 소개",
#         )
#
#     def test_get_idol_list(self):
#         url = reverse("idols:idol-list")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertGreater(len(response.data), 0)
#         self.assertEqual(response.data[0]["name"], "테스트아이돌")
#
#     def test_create_idol(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         url = reverse("idols:idol-list")
#         data = {
#             "name": "새아이돌",
#             "description": "새로운 아이돌 소개",
#         }
#         response = self.client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data["name"], "새아이돌")
#
#     def test_get_idol_detail(self):
#         url = reverse("idols:idol-detail", kwargs={"pk": self.idol.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["name"], "테스트아이돌")
#
#     def test_update_idol(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         url = reverse("idols:idol-detail", kwargs={"pk": self.idol.pk})
#         data = {"name": "수정아이돌"}
#         response = self.client.patch(url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["name"], "수정아이돌")
#
#     def test_delete_idol(self):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
#         url = reverse("idols:idol-detail", kwargs={"pk": self.idol.pk})
#         response = self.client.delete(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertFalse(Idol.objects.filter(pk=self.idol.pk, is_active=True).exists())
