from drf_yasg import openapi
from drf_yasg.utils import force_real_str, swagger_auto_schema

from utils.responses.idol import (
    IDOL_CREATE_SERVER_ERROR,
    IDOL_CREATE_SUCCESS,
    IDOL_CREATE_VALIDATION_FAIL,
    IDOL_DELETE_FAIL,
    IDOL_DELETE_SUCCESS,
    IDOL_DETAIL_SUCCESS,
    IDOL_LIST_SUCCESS,
    IDOL_SEARCH_NOT_FOUND,
    IDOL_SEARCH_SUCCESS,
    IDOL_UPDATE_FAIL,
    IDOL_UPDATE_SERVER_ERROR,
    IDOL_UPDATE_SUCCESS,
)

# 아이돌 검색
idol_search_docs = swagger_auto_schema(
    operation_summary="아이돌 검색",
    operation_description="아이돌 이름으로 검색합니다.",
    responses={
        200: force_real_str(IDOL_SEARCH_SUCCESS),
        400: force_real_str(IDOL_SEARCH_NOT_FOUND),
    },
    tags=["아이돌/검색"],
)

# 아이돌 생성
idol_create_docs = swagger_auto_schema(
    operation_summary="아이돌 생성",
    operation_description="새로운 아이돌을 생성합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["name", "description"],
        properties={
            "name": openapi.Schema(type=openapi.TYPE_STRING, description="아이돌 이름"),
            "debut_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="데뷔일 (선택)",
            ),
            "agency": openapi.Schema(
                type=openapi.TYPE_STRING, description="소속사 (선택)"
            ),
            "description": openapi.Schema(
                type=openapi.TYPE_STRING, description="아이돌 소개"
            ),
        },
    ),
    responses={
        201: force_real_str(IDOL_CREATE_SUCCESS),
        400: force_real_str(IDOL_CREATE_VALIDATION_FAIL),
        401: "인증되지 않은 사용자",
        500: force_real_str(IDOL_CREATE_SERVER_ERROR),
    },
    tags=["아이돌/관리"],
)

# 아이돌 목록 조회
idol_list_docs = swagger_auto_schema(
    operation_summary="아이돌 목록 조회",
    operation_description="모든 아이돌의 목록을 조회합니다.",
    responses={
        200: force_real_str(IDOL_LIST_SUCCESS),
    },
    tags=["아이돌/조회"],
)

# 아이돌 상세 조회
idol_retrieve_docs = swagger_auto_schema(
    operation_summary="아이돌 상세 조회",
    operation_description="특정 아이돌의 상세 정보를 조회합니다.",
    responses={
        200: force_real_str(IDOL_DETAIL_SUCCESS),
        404: "아이돌을 찾을 수 없음",
    },
    tags=["아이돌/조회"],
)

# 아이돌 정보 수정
idol_update_docs = swagger_auto_schema(
    operation_summary="아이돌 정보 수정",
    operation_description="특정 아이돌의 정보를 수정합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "name": openapi.Schema(type=openapi.TYPE_STRING, description="아이돌 이름"),
            "debut_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="데뷔일 (선택)",
            ),
            "agency": openapi.Schema(
                type=openapi.TYPE_STRING, description="소속사 (선택)"
            ),
            "description": openapi.Schema(
                type=openapi.TYPE_STRING, description="아이돌 소개"
            ),
        },
    ),
    responses={
        200: force_real_str(IDOL_UPDATE_SUCCESS),
        400: force_real_str(IDOL_UPDATE_FAIL),
        401: "인증되지 않은 사용자",
        404: "아이돌을 찾을 수 없음",
        500: force_real_str(IDOL_UPDATE_SERVER_ERROR),
    },
    tags=["아이돌/관리"],
)

# 아이돌 삭제
idol_delete_docs = swagger_auto_schema(
    operation_summary="아이돌 삭제",
    operation_description="특정 아이돌을 삭제합니다.",
    responses={
        200: force_real_str(IDOL_DELETE_SUCCESS),
        400: force_real_str(IDOL_DELETE_FAIL),
        401: "인증되지 않은 사용자",
        404: "아이돌을 찾을 수 없음",
    },
    tags=["아이돌/관리"],
)

# # 아이돌 활성화/비활성화 관련 응답 상수
# IDOL_ACTIVATE_SUCCESS = {
#     "code": 200,
#     "message": "아이돌 활성화 성공",
#     "data": None,
# }
# IDOL_DEACTIVATE_SUCCESS = {
#     "code": 200,
#     "message": "아이돌 비활성화 성공",
#     "data": None,
# }

# # 아이돌 활성화
# idol_activate_docs = swagger_auto_schema(
#     operation_summary="아이돌 활성화",
#     operation_description="아이돌 정보를 활성화 상태로 변경합니다.",
#     responses={
#         200: force_real_str(IDOL_UPDATE_SUCCESS),
#     },
# )

# # 아이돌 비활성화
# idol_deactivate_docs = swagger_auto_schema(
#     operation_summary="아이돌 비활성화",
#     operation_description="아이돌 정보를 비활성화 상태로 변경합니다.",
#     responses={
#         200: force_real_str(IDOL_UPDATE_SUCCESS),
#     },
# )
