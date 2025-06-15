from rest_framework import permissions


# 대상에 대한 소유 확인
class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        # permissions.SAFE_METHODS : 읽기 전용 HTTP 메서드 목록 ('GET', 'HEAD', 'OPTIONS')
        if request.method in permissions.SAFE_METHODS:
            return True

        # 어떤 종류의 View든 상관없이 get_object()를 유연하게 호출하기 위해 사용
        try:  # APIView만 쓸 때
            obj = view.get_object(request, *view.args, **view.kwargs)
        except TypeError:  # generic 쓸 때
            obj = view.get_object()

        # obj = view.get_object(request, *view.args, **view.kwargs)
        if hasattr(obj, "author"):
            return request.user == obj.author
        else:
            return False
