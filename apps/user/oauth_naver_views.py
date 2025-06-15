# from urllib.parse import urlencode
#
# import requests
# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.core import signing
# from django.http import Http404, JsonResponse
# from django.shortcuts import redirect, render
# from django.views.generic import RedirectView
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.tokens import RefreshToken
#
# from utils.csrf import generate_csrf_token
# from utils.random_nickname import generate_unique_numbered_nickname
#
# User = get_user_model()
#
# NAVER_CALLBACK_URL = "/api/users/naver/callback"
# NAVER_STATE = "naver_login"
# NAVER_LOGIN_URL = "https://nid.naver.com/oauth2.0/authorize"
# NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
# NAVER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"
#
# # [사용자] → [프론트: React] → [네이버 로그인] → [백엔드: Django 콜백 + 토큰 발급] → [프론트: JWT 저장]
#
#
# class NaverLoginRedirectView(RedirectView):
#     def get_redirect_url(self, *args, **kwargs):
#         domain = self.request.scheme + "://" + self.request.META.get("HTTP_HOST", "")
#         domain = domain.replace("localhost", "127.0.0.1")
#         callback_url = domain + NAVER_CALLBACK_URL
#         state = signing.dumps(NAVER_STATE)
#         # print("state", state)
#         # print("test-get_host", self.request.get_host())  # 127.0.0.1:8000
#         # print("test-get_port", self.request.get_port())  # 8000
#         # # print("test-getvalue", self.request.getvalue())  # 안됨
#         # # print("test-getbuffer", self.request.getbuffer())  # 안됨
#         # print("test-get_full_path", self.request.get_full_path())  # /api/users/naver/login?name=tae
#         # print("test-get_full_path_info", self.request.get_full_path_info())  # /api/users/naver/login?name=tae
#         # # print("test-get_signed_cookie", self.request.get_signed_cookie())  # 안됨
#
#         params = {
#             "response_type": "code",
#             "client_id": settings.NAVER_CLIENT_ID,
#             "redirect_uri": callback_url,
#             "state": state,
#         }
#         # print(f"{NAVER_LOGIN_URL}?{urlencode(params)}")
#         return f"{NAVER_LOGIN_URL}?{urlencode(params)}"
#
#
# def naver_callback(request):
#     code = request.GET.get("code")
#     state = request.GET.get("state")
#
#     if NAVER_STATE != signing.loads(state):
#         raise Http404
#
#     access_token = get_naver_access_token(code, state)
#     profile = get_naver_profile(access_token)
#     email = profile.get("email")
#     print("profile123", profile)
#
#     if not email:
#         params = urlencode({"error": "이메일을 가져올 수 없습니다."})
#         return redirect(f"{settings.FRONTEND_URL}/oauth/failure?{params}")
#
#     user = User.objects.filter(email=email).first()
#
#     if not user:
#         name = profile.get("name", "")
#         nickname = profile.get("nickname", None)
#         # random_pw = User.objects.make_random_password()
#         random_pw = "qwer1234!"
#
#         if not nickname:
#             nickname = generate_unique_numbered_nickname()
#         try:
#             user = User.objects.create_user(
#                 email=email, password=random_pw, name=name, nickname=nickname, is_active=True
#             )
#         except:
#             params = urlencode({"error": "회원을 생성할 수 없습니다."})
#             return redirect(f"{settings.FRONTEND_URL}/oauth/failure?{params}")
#
#     # 커스텀 CSRF 토큰 발급
#     csrf_token = generate_csrf_token()
#
#     # JWT 토큰 발급
#     refresh_token = RefreshToken.for_user(user)
#     access_token = refresh_token.access_token
#
#     # 프론트로 토큰 전달
#     params = urlencode({"access_token": access_token, "csrf_token": csrf_token})
#     redirect_response = redirect(f"{settings.FRONTEND_URL}/oauth/callback-test?{params}")
#
#     # 쿠키 추가
#     redirect_response.set_cookie(
#         key="refresh_token",
#         value=str(refresh_token),
#         httponly=True,
#         # secure=True,        # HTTPS 환경에서만 전송
#         secure=False,  # 로컬 개발 환경에 맞춰서 설정
#         samesite="Lax",  # CSRF 공격 방지 설정
#         path="/api/users/token",  # 필요한 경로에만 쿠키 사용
#         max_age=60 * 60 * 24 * 1,  # 1일 (초 단위)
#     )
#
#     return redirect_response
#
#     # # 유저가 있다면 로그인
#     # if user:
#     #     # 유저가 활성화 되지 않았으면 활성화
#     #     if not user.is_active:
#     #         user.is_active = True
#     #         user.save()
#     #
#     #     # JWT 토큰 발급
#     #     refresh = RefreshToken.for_user(user)
#     #     access = str(refresh.access_token)
#     #
#     #     # 프론트로 토큰 전달
#     #     frontend_url = settings.FRONTEND_URL
#     #     return redirect(
#     #         f"{frontend_url}/oauth/callback?access={access}&refresh={str(refresh)}"
#     #     )
#     #
#     # # 유저가 없다면 프론트에서 닉네임 받아서 별도 API로 회원가입
#     # frontend_url = settings.FRONTEND_URL
#     # return redirect(
#     #     f"{frontend_url}/oauth/callback?access_token={access_token}&oauth=naver"
#     # )
#
#
# def get_naver_access_token(code, state):
#     params = {
#         "grant_type": "authorization_code",
#         "client_id": settings.NAVER_CLIENT_ID,
#         "client_secret": settings.NAVER_CLIENT_SECRET,
#         "code": code,
#         "state": state,
#     }
#
#     response = requests.get(NAVER_TOKEN_URL, params=params)
#     result = response.json()
#     print("get_naver_access_token", result)
#     return result.get("access_token")
#
#
# def get_naver_profile(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     response = requests.get(NAVER_PROFILE_URL, headers=headers)
#
#     if response.status_code != 200:
#         raise Http404
#
#     result = response.json()
#     print("get_naver_profile", result)
#     return result.get("response")
#
#
# # class OAuthSignupView(APIView):
# #     def post(self, request):
# #         access_token = request.data.get("access_token")
# #         nickname = request.data.get("nickname")
# #         oauth = request.data.get("oauth")
# #
# #         if oauth != "naver":
# #             return Response({"message": "지원하지 않는 소셜 로그인입니다."}, status=400)
# #
# #         if not access_token or not nickname:
# #             return Response({"message": "필수 값이 누락되었습니다."}, status=400)
# #
# #         profile = get_naver_profile(access_token)
# #         email = profile.get("email")
# #
# #         if not email or User.objects.filter(email=email).exists():
# #             return Response({"message": "이미 가입된 이메일입니다."}, status=400)
# #
# #         user = User(email=email, nickname=nickname, is_active=True)
# #         random_pw = User.objects.make_random_password()
# #         user.set_password(random_pw)
# #         user.save()
# #
# #         refresh = RefreshToken.for_user(user)
# #         return Response(
# #             {
# #                 "message": "회원가입 성공",
# #                 "access": str(refresh.access_token),
# #                 "refresh": str(refresh),
# #             },
# #             status=201,
# #         )
#
#
# def naver_login_test_page(request):
#     return render(request, "naver_test.html")
#
#
# def oauth_callback_test_page(request):
#     return render(request, "oauth_callback_test.html")
#
#
# # Naver 로그인 리턴값
# # {
# #   "resultcode": "00",
# #   "message": "success",
# #   "response": {
# #     "id": "U3V2ZGF3ZXNvbWU=",
# #     "email": "testuser@naver.com",
# #     "name": "테스트유저",
# #     "nickname": "테스트",
# #     "profile_image": "https://...",
# #     "age": "20-29",
# #     "gender": "M",
# #     "birthday": "10-01",
# #     "birthyear": "1999",
# #     "mobile": "010-1234-5678"
# #   }
# # }
