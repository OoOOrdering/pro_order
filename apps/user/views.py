from django.conf import settings
from django.core import signing
from django.core.signing import SignatureExpired, TimestampSigner
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user.models import User
from apps.user.serializers import (
    LogoutSerializer,
    PasswordCheckSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
)
from utils.csrf import generate_csrf_token, validate_csrf_token
from utils.email import send_email
from utils.responses.user import (
    CSRF_INVALID_TOKEN,
    INVALID_REFRESH_TOKEN,
    INVALID_SIGNATURE,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LOGOUT_SUCCESS,
    MISSING_REFRESH_TOKEN,
    PASSWORD_CHECK_INVALID,
    PASSWORD_MATCH_SUCCESS,
    PASSWORD_NOT_MATCH,
    PROFILE_DELETE_RESPONSE,
    PROFILE_RETRIEVE_RESPONSE,
    PROFILE_UPDATE_RESPONSE,
    SIGNATURE_EXPIRED,
    SIGNUP_PASSWORD_MISMATCH,
    SIGNUP_SUCCESS,
    TOKEN_REFRESH_RESPONSE,
    VERIFY_EMAIL_ALREADY_VERIFIED,
    VERIFY_EMAIL_SUCCESS,
    WEAK_PASSWORD,
)


# 회원 가입
class RegisterView(CreateAPIView):
    queryset = User.objects.all()  # Model
    serializer_class = RegisterSerializer  # Serializer

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="회원가입",
        operation_description="",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER, example=SIGNUP_SUCCESS["code"]
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING, example=SIGNUP_SUCCESS["message"]
                    ),
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            "email": openapi.Schema(
                                type=openapi.TYPE_STRING, example="test@example.com"
                            ),
                            "name": openapi.Schema(
                                type=openapi.TYPE_STRING, example="taejin"
                            ),
                            "nickname": openapi.Schema(
                                type=openapi.TYPE_STRING, example="Lululala"
                            ),
                            "verify_url": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="http://localhost:8000/api/users/verify/email?code=signed_code",
                            ),
                        },
                    ),
                },
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        example=SIGNUP_PASSWORD_MISMATCH["code"],
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example=f'{SIGNUP_PASSWORD_MISMATCH["message"]} or {WEAK_PASSWORD["message"]}',
                    ),
                    "data": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example=f'None or "This password is too short" or "It must contain at least 8 characters." or "This password is too common"',
                    ),
                },
            ),
        },
    )
    def post(
        self, request, *args, **kwargs
    ):  # 스웨거 데코레이터 사용하기 위해 오버라이드(원래 동작과 동일)
        return self.create(
            request, *args, **kwargs
        )  # CreateAPIView가 내부적으로 사용하는 create 호출

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 이메일 서명
        signer = TimestampSigner()

        # 1. 이메일에 서명
        signed_email = signer.sign(user.email)
        # 2. 서명된 이메일을 직렬화
        signed_code = signing.dumps(signed_email)

        # signed_code = signer.sign(user.email)

        verify_url = f"{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}"

        subject = "[WiStar] 이메일 인증을 완료해주세요."
        message = f"아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}"
        send_email(subject, message, user.email)

        response_data = serializer.data
        custom_response = SIGNUP_SUCCESS

        if settings.DEBUG:
            # 응답에 verify_url 포함
            response_data["verify_url"] = verify_url

        custom_response["data"] = response_data

        return Response(custom_response, status=status.HTTP_201_CREATED)


# 이메일 인증
class VerifyEmailView(APIView):

    @swagger_auto_schema(
        tags=["유저/인증"],
        operation_summary="이메일 인증 링크 확인",
        # manual_parameters=[
        #     openapi.Parameter(
        #         "code",
        #         openapi.IN_QUERY,
        #         description="이메일에 첨부된 서명된 인증 코드",
        #         type=openapi.TYPE_STRING,
        #         required=True,
        #         example="(코드만입력)c2lnbmVkX2NvZGVkX2VtYWls",
        #     )
        # ],
        responses={
            200: openapi.Response(
                description="이메일 인증 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=VERIFY_EMAIL_SUCCESS["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=VERIFY_EMAIL_SUCCESS["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            400: openapi.Response(
                description="유효하지 않은 서명",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER, example=INVALID_SIGNATURE["code"]
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=INVALID_SIGNATURE["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            410: openapi.Response(
                description="인증 코드 만료",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER, example=SIGNATURE_EXPIRED["code"]
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=SIGNATURE_EXPIRED["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def get(self, request):
        code = request.GET.get("code", "")
        signer = TimestampSigner()
        try:
            # 3. 직렬화된 데이터를 역직렬화
            decoded_user_email = signing.loads(code)
            # 4. 타임스탬프 유효성 검사 포함하여 복호화
            email = signer.unsign(decoded_user_email, max_age=60 * 5)  # 5분 설정

        # except Exception as e:  # 이렇게 처리 많이 하지만 에러를 지정해서 하는게 제일 좋음.
        except SignatureExpired:  # 시간 지나서 오류발생하면 오류처리
            return JsonResponse(SIGNATURE_EXPIRED, status=status.HTTP_410_GONE)
        except Exception:
            return Response(INVALID_SIGNATURE, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, email=email)

        if user.is_active:
            return Response(VERIFY_EMAIL_ALREADY_VERIFIED, status=status.HTTP_200_OK)

        user.is_active = True
        user.save()
        return Response(VERIFY_EMAIL_SUCCESS, status=status.HTTP_200_OK)


# 로그인
class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="JWT 로그인",
        operation_description="로그인 후 access_token + csrf_token 응답, refresh_token은 HttpOnly 쿠키로 저장됨",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER, example=LOGIN_SUCCESS["code"]
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING, example=LOGIN_SUCCESS["message"]
                    ),
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                            "csrf_token": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                },
            ),
            401: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER, example=LOGIN_FAILED["code"]
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING, example=LOGIN_FAILED["message"]
                    ),
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)

            tokens = response.data
            access_token = tokens.get("access")
            refresh_token = tokens.get("refresh")

            # 커스텀 CSRF 토큰 발급
            csrf_token = generate_csrf_token()
            # csrf_token = get_token(request)

            custom_response = LOGIN_SUCCESS
            custom_response["data"] = {
                "access_token": access_token,
                "csrf_token": csrf_token,
            }

            # Refresh Token을 HttpOnly 쿠키로 설정
            final_response = Response(custom_response, status=status.HTTP_200_OK)
            final_response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,  # HTTPS 환경에서만 전송
                # secure=False,  # 로컬 개발 환경에 맞춰서 설정
                samesite="Lax",  # CSRF 공격 방지 설정
                path="/api/users/token",  # 필요한 경로에만 쿠키 사용
                max_age=60 * 60 * 24 * 1,  # 1일 (초 단위)
            )

            return final_response
        except AuthenticationFailed as e:
            # SimpleJWT가 raise하는 예외
            return Response(LOGIN_FAILED, status=status.HTTP_401_UNAUTHORIZED)


# class LogoutAPIView(CreateAPIView):
#     # permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
#     permission_classes = []  # 인증 없이 호출 가능
#     serializer_class = LogoutSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"detail": "로그아웃되었습니다."}, status=status.HTTP_205_RESET_CONTENT)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 로그아웃
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = []  # 인증 없이 호출 가능

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="JWT 로그아웃",
        operation_description="HttpOnly 쿠키에서 refresh_token을 삭제하고, 블랙리스트에 등록합니다.",
        request_body=None,
        # manual_parameters=[
        #     openapi.Parameter(
        #         name="Authorization",
        #         in_=openapi.IN_HEADER,
        #         type=openapi.TYPE_STRING,
        #         description="Bearer 액세스 토큰 (예: Bearer eyJs1j2jx...)",
        #         required=True,
        #         example="Bearer <access_token>",
        #     ),
        # ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER, example=LOGOUT_SUCCESS["code"]
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING, example=LOGOUT_SUCCESS["message"]
                    ),
                    "data": None,
                },
            ),
            401: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER, example=MISSING_REFRESH_TOKEN["code"]
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example=f'{MISSING_REFRESH_TOKEN["message"]} or {INVALID_REFRESH_TOKEN["message"]}',
                    ),
                    "data": None,
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):

        # token = request.headers.get('X-CSRFToken')
        #
        # if not validate_csrf_token(token):
        #     raise PermissionDenied(CSRF_VALIDATION_FAILED)

        # 쿠키에서 Refresh Token 가져오기
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(MISSING_REFRESH_TOKEN, status=status.HTTP_401_UNAUTHORIZED)

        serializer = LogoutSerializer(data={"refresh_token": refresh_token})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 쿠키 삭제
        response = Response(LOGOUT_SUCCESS, status=status.HTTP_200_OK)
        response.delete_cookie(
            "refresh_token", path="/api/users/token"
        )  # Path 일치해야 함

        return response


# 엑세스 토큰 리프레시
class CustomTokenRefreshView(APIView):
    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="액세스 토큰 재발급",
        operation_description="(스웨거에서 테스트 불가) HttpOnly 쿠키에 저장된 리프레시 토큰으로 새로운 액세스 토큰과 CSRF 토큰을 재발급합니다.",
        request_body=None,
        manual_parameters=[
            openapi.Parameter(
                name="X-CSRFToken",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="CSRF 토큰",
                required=True,
                example="yJhbGciOiJIUzI1NiIs...",
            ),
        ],
        responses={
            200: openapi.Response(
                description="토큰 재발급 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=TOKEN_REFRESH_RESPONSE["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=TOKEN_REFRESH_RESPONSE["message"],
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                ),
                                "csrf_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="newly_generated_csrf_token_abc123",
                                ),
                            },
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="리프레시 토큰이 누락되었거나 유효하지 않음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=MISSING_REFRESH_TOKEN["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=MISSING_REFRESH_TOKEN["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            403: openapi.Response(
                description="CSRF 토큰이 누락되었거나 유효하지 않음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=CSRF_INVALID_TOKEN["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=CSRF_INVALID_TOKEN["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        # CSRF 토큰 검증
        csrf_token = request.headers.get("X-CSRFToken")
        if not csrf_token or not validate_csrf_token(csrf_token):
            return Response(CSRF_INVALID_TOKEN, HTTP_403_FORBIDDEN)

        # 리프레시 토큰 쿠키에서 가져오기
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(MISSING_REFRESH_TOKEN, HTTP_401_UNAUTHORIZED)

        # SimpleJWT Serializer로 Access Token 재발급
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        new_access_token = serializer.validated_data.get("access")

        # 새로운 커스텀 CSRF 토큰 발급 (선택)
        new_csrf_token = generate_csrf_token()

        # 새로운 리프레시 토큰이 있다면 (ROTATE 설정 시)
        new_refresh_token = serializer.validated_data.get("refresh")

        # 응답 데이터 구성
        custom_response = TOKEN_REFRESH_RESPONSE
        custom_response["data"] = {
            "access_token": new_access_token,
            "csrf_token": new_csrf_token,
        }

        # 최종 응답
        final_response = Response(custom_response, status=status.HTTP_200_OK)

        # 새 리프레시 토큰이 있을 때만 쿠키에 다시 설정
        if new_refresh_token:
            final_response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=False,  # 로컬 개발환경
                samesite="Lax",
                path="/api/users/token",
                max_age=60 * 60 * 24 * 1,
            )

        return final_response


# 유저 수정
class ProfileView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    # serializer_class = UserMeReadSerializer
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 인증

    http_method_names = ["get", "patch", "delete"]  # ← PUT 제외

    def get_object(self):
        # DRF 기본 동작
        # URL 통해 넘겨 받은 pk를 통해 queryset에 데이터를 조회
        # -> User.objects.all()
        return self.request.user  # 인증이 끝난 유저가 들어감.

    def get_serializer_class(self):
        # HTTP 메소드 별로 다른 Serializer 적용
        # -> 각 요청마다 입/출력에 사용되는 데이터의 형식이 다르기 때문

        if self.request.method == "GET":
            return ProfileSerializer

        elif self.request.method == "PATCH":
            return ProfileUpdateSerializer

        return super().get_serializer_class()

    @swagger_auto_schema(
        tags=["유저/프로필"],
        operation_summary="내 프로필 조회",
        request_body=None,
        # manual_parameters=[
        #     openapi.Parameter(
        #         name="Authorization",
        #         in_=openapi.IN_HEADER,
        #         type=openapi.TYPE_STRING,
        #         description="Bearer 액세스 토큰 (예: Bearer eyJs1j2jx...)",
        #         required=True,
        #         example="Bearer <access_token>",
        #     ),
        # ],
        responses={
            200: ProfileSerializer,
            401: openapi.Response(
                description="JWT 인증 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=401),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING, example="인증 정보가 없습니다."
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({**PROFILE_RETRIEVE_RESPONSE, "data": serializer.data})

    @swagger_auto_schema(
        tags=["유저/프로필"],
        operation_summary="내 프로필 수정",
        request_body=ProfileUpdateSerializer,
        # manual_parameters=[
        #     openapi.Parameter(
        #         name="Authorization",
        #         in_=openapi.IN_HEADER,
        #         type=openapi.TYPE_STRING,
        #         description="Bearer 액세스 토큰 (예: Bearer eyJs1j2jx...)",
        #         required=True,
        #         example="Bearer <access_token>",
        #     ),
        # ],
        responses={
            200: openapi.Response(
                description="프로필 수정 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="회원정보가 수정되었습니다.",
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "nickname": openapi.Schema(
                                    type=openapi.TYPE_STRING, example="taejin"
                                ),
                                "profile_image": openapi.Schema(
                                    type=openapi.TYPE_STRING, example="https://..."
                                ),
                                "comment_alarm": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN, example=True
                                ),
                                "like_alarm": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN, example=False
                                ),
                                "schedule_alarm": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN, example=True
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="유효하지 않은 입력",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=400),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="닉네임은 필수 항목입니다.",
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(
            {
                **PROFILE_UPDATE_RESPONSE,
                "data": serializer.data,
            }
        )

    @swagger_auto_schema(
        tags=["유저/프로필"],
        operation_summary="회원 탈퇴",
        request_body=None,
        # manual_parameters=[
        #     openapi.Parameter(
        #         name="Authorization",
        #         in_=openapi.IN_HEADER,
        #         type=openapi.TYPE_STRING,
        #         description="Bearer 액세스 토큰 (예: Bearer eyJs1j2jx...)",
        #         required=True,
        #         example="Bearer <access_token>",
        #     ),
        # ],
        responses={
            200: openapi.Response(
                description="회원 탈퇴 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="회원 탈퇴가 완료되었습니다.",
                        ),
                        "data": None,
                    },
                ),
            ),
            401: openapi.Response(
                description="JWT 인증 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=401),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING, example="인증 정보가 없습니다."
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):

        user = self.get_object()
        user.delete()
        return Response(PROFILE_DELETE_RESPONSE, status=status.HTTP_200_OK)


class PasswordCheckView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 인증

    @swagger_auto_schema(
        tags=["유저/인증"],
        operation_summary="비밀번호 확인",
        operation_description="입력한 비밀번호가 현재 사용자 계정의 비밀번호와 일치하는지 확인합니다.",
        request_body=PasswordCheckSerializer,
        responses={
            200: openapi.Response(
                description="비밀번호 일치",
                examples={"application/json": PASSWORD_MATCH_SUCCESS},
            ),
            400: openapi.Response(
                description="비밀번호 불일치 또는 입력값 오류",
                examples={"application/json": PASSWORD_NOT_MATCH},
            ),
        },
        security=[{"Bearer": []}],
    )
    def post(self, request):
        serializer = PasswordCheckSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data["password"]
            user = request.user

            if user.check_password(password):
                return Response(PASSWORD_MATCH_SUCCESS, status=status.HTTP_200_OK)
            return Response(PASSWORD_NOT_MATCH, status=status.HTTP_400_BAD_REQUEST)

        password_check_invalid = PASSWORD_CHECK_INVALID
        password_check_invalid["data"] = serializer.errors
        return Response(password_check_invalid, status=status.HTTP_400_BAD_REQUEST)


# 토큰 정보 확인
# https://jwt.io/
