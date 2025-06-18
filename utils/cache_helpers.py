import logging

from django.core.cache import cache

from utils.cache_keys import get_user_list_cache_key, get_user_profile_cache_key

logger = logging.getLogger(__name__)


def invalidate_user_cache(user_id):
    """
    사용자 관련 모든 캐시를 무효화합니다.

    Args:
    ----
        user_id: 사용자 ID

    """
    try:
        # 프로필 캐시 무효화
        profile_key = get_user_profile_cache_key(user_id)
        cache.delete(profile_key)

        # 리스트 캐시 무효화 (1~10페이지 예시)
        for page in range(1, 11):
            list_key = get_user_list_cache_key(page)
            cache.delete(list_key)

        logger.info(f"User cache invalidated for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Cache invalidation failed for user_id {user_id}: {e!s}")
        raise


def invalidate_all_user_caches():
    """모든 사용자 관련 캐시를 무효화합니다."""
    try:
        # 프로필 캐시 무효화
        cache.delete_pattern("user_profile_*")

        # 리스트 캐시 무효화
        cache.delete_pattern("user_list_*")

        logger.info("All user caches invalidated")
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e!s}")
        raise
