# utils/responses/idol.py

# GET /api/idols?name=abc
IDOL_SEARCH_SUCCESS = {
    "code": 200,
    "message": "아이돌 검색 성공",
    "data": [
        {
            "idol_id": 100,
            "name": "오즈코딩",
            "debut_date": "2024-04-23",
            "agency": "오즈엔터",
            "description": "코딩 공부하는 아이돌",
            "profile_image": "아이돌 프로필 이미지 URL",
        }
    ],
}
IDOL_SEARCH_NOT_FOUND = {
    "code": 400,
    "message": "아이돌 정보를 찾을 수 없습니다.",
    "data": None,
}


# GET /api/idols
IDOL_LIST_SUCCESS = {
    "code": 200,
    "message": "아이돌 목록",
    "data": [],
}
IDOL_LIST_NOT_FOUND = {
    "code": 400,
    "message": "아이돌 정보가 존재하지 않습니다.",
    "data": None,
}


# POST /api/idols
IDOL_CREATE_SUCCESS = {
    "code": 201,
    "message": "아이돌 등록 성공",
    "data": {
        "idol_id": 100,
        "name": "오즈코딩",
        "en_name": "ozcoding",
        "debut_date": "2024-04-23",
        "agency": "오즈엔터",
        "description": "코딩 공부하는 아이돌",
        "profile_image": "아이돌 프로필 이미지 URL",
        "created_at": "2025-04-23T01:00:00Z",
        "updated_at": "2025-04-23T01:00:00Z",
    },
}
IDOL_CREATE_VALIDATION_FAIL = {
    "code": 400,
    "message": "아이돌 등록에 실패했습니다.",
    "data": None,
}
IDOL_CREATE_SERVER_ERROR = {
    "code": 500,
    "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    "data": None,
}


# GET /api/idols/{idol_id}
IDOL_DETAIL_SUCCESS = {
    "code": 200,
    "message": "아이돌 정보 조회 성공",
    "data": {
        "idol_id": 100,
        "name": "오즈코딩",
        "debut_date": "2024-04-23",
        "agency": "오즈엔터",
        "description": "코딩 팀치는 아이돌",
        "profile_image": "프로필 이미지 URL",
    },
}
IDOL_DETAIL_NOT_FOUND = {
    "code": 400,
    "message": "아이돌 정보를 찾을 수 없습니다.",
    "data": None,
}


# PATCH /api/idols/{idol_id}
IDOL_UPDATE_SUCCESS = {
    "code": 200,
    "message": "아이돌 정보 수정 성공",
    "data": {
        "idol_id": 100,
        "name": "오즈코딩",
        "debut_date": "2024-04-23",
        "agency": "오즈엔터",
        "description": "코딩 팀치는 아이돌",
        "profile_image": "프로필 이미지 URL",
        "updated_at": "2025-04-23T13:45:00Z",
    },
}
IDOL_UPDATE_FAIL = {
    "code": 400,
    "message": "수정 권한이 없습니다.",
    "data": None,
}
IDOL_UPDATE_SERVER_ERROR = {
    "code": 500,
    "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    "data": None,
}


# DELETE /api/idols/{idol_id}
IDOL_DELETE_SUCCESS = {
    "code": 200,
    "message": "아이돌 삭제 성공",
    "data": None,
}
IDOL_DELETE_FAIL = {
    "code": 400,
    "message": "삭제 권한이 없습니다.",
    "data": None,
}
