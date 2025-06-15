# utils/messages.py

from rest_framework import status

# 공통 성공 응답
FOLLOW_LIST_SUCCESS = {
    "code": status.HTTP_200_OK,
    "message": "팔로우 목록 조회 성공",
}

FOLLOW_STATUS_SUCCESS = {
    "code": status.HTTP_200_OK,
    "message": "팔로우 여부 조회 성공",
}

FOLLOW_CREATE_SUCCESS = {
    "code": status.HTTP_201_CREATED,
    "message": "아이돌 팔로우 성공",
}

FOLLOW_DELETE_SUCCESS = {
    "code": 204,
    "message": "아이돌 언팔로우 성공",
    "data": None,
}

# 공통 에러 응답
FOLLOW_ALREADY_EXISTS = {
    "code": 400,
    "message": "이미 팔로우 중입니다.",
    "data": None,
}

FOLLOW_NOT_FOUND = {
    "code": 404,
    "message": "팔로우하지 않았습니다.",
    "data": None,
}
