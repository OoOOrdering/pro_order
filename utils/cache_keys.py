USER_PROFILE_CACHE_TIMEOUT = 300  # 5분
USER_LIST_CACHE_TIMEOUT = 120  # 2분


def get_user_profile_cache_key(user_id):
    """사용자 프로필 캐시 키를 생성합니다."""
    return f"user_profile_{user_id}"


def get_user_list_cache_key(page=1, filters=None):
    """사용자 리스트 캐시 키를 생성합니다.

    필터 조건이 있으면 키에 포함합니다.
    """
    filters_str = ""
    if filters:
        filters_str = "_".join(f"{k}:{v}" for k, v in sorted(filters.items()))
    return f"user_list_{page}_{filters_str}"
