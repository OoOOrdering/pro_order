from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.user.models import User


# 유저 추가용 폼
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "nickname", "name")


# 유저 수정용 폼
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "nickname", "name", "is_active", "is_staff", "is_superuser")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = (
        "id",
        "email",
        "nickname",
        "name",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
        "updated_at",
    )  # 관리자 목록 페이지에 보여줄 컬럼
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )  # 필터 사이드바에 표시할 필드
    search_fields = ("email", "nickname", "name")  # 검색창을 통해 검색할 수 있는 필드
    ordering = ("-created_at",)  # 생성일 기준으로 최신순 정렬
    list_display_links = (
        "email",
        "nickname",
        "name",
    )  # 목록에서 content를 클릭하면 상세 페이지로 이동
    readonly_fields = ("created_at", "updated_at")

    def get_fieldsets(self, request, obj=None):
        if not obj:
            # 유저 추가 페이지
            return (
                (
                    "기본 정보",
                    {"fields": ("email", "nickname", "name", "password1", "password2")},
                ),
                ("권한", {"fields": ("is_active", "is_staff", "is_superuser")}),
            )
        # 유저 수정 페이지
        return (
            ("기본 정보", {"fields": ("email", "nickname", "name")}),
            ("권한", {"fields": ("is_active", "is_staff", "is_superuser")}),
            ("기타 정보", {"fields": ("created_at", "updated_at")}),
        )

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = self.add_form
        else:
            kwargs["form"] = self.form
        return super().get_form(request, obj, **kwargs)
