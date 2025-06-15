from rest_framework import status

# 조회
SCHEDULE_LIST_SUCCESS = {
    "code": 200,
    "message": "사용자 + 팔로우 아이돌 일정 목록 조회 성공",
    "status": status.HTTP_200_OK,
}

SCHEDULE_DETAIL_SUCCESS = {
    "code": 200,
    "message": "사용자 일정 조회 성공",
    "status": status.HTTP_200_OK,
}

# 생성
SCHEDULE_CREATE_SUCCESS = {
    "code": 201,
    "message": "사용자 일정 등록 성공",
    "status": status.HTTP_201_CREATED,
}

# 수정
SCHEDULE_UPDATE_SUCCESS = {
    "code": 200,
    "message": "일정 수정 성공",
    "status": status.HTTP_200_OK,
}

# 삭제
SCHEDULE_DELETE_SUCCESS = {
    "code": 204,
    "message": "일정 삭제 성공",
    "status": status.HTTP_204_NO_CONTENT,
}

# 예외
SCHEDULE_NO_PERMISSION = {
    "code": 403,
    "message": "해당 일정에 대한 권한이 없습니다.",
    "status": status.HTTP_403_FORBIDDEN,
}

SCHEDULE_NOT_FOUND = {
    "code": 404,
    "message": "일정을 찾을 수 없습니다.",
    "status": status.HTTP_404_NOT_FOUND,
}
