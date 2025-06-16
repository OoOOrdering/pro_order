from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """객체의 소유자나 관리자만 접근을 허용하는 권한 클래스."""

    def has_object_permission(self, request, view, obj):
        # 관리자는 모든 작업 가능
        if request.user.is_staff:
            return True

        # 객체의 소유자만 접근 가능
        return obj == request.user

    def has_permission(self, request, view):
        # 인증된 사용자만 접근 가능
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    """관리자는 모든 작업 가능, 일반 사용자는 읽기만 가능한 권한 클래스."""

    def has_permission(self, request, view):
        # 읽기 작업은 모든 인증된 사용자에게 허용
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # 쓰기 작업은 관리자만 허용
        return request.user and request.user.is_staff
