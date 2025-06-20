from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User

from .models import DashboardSummary


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com", password="testpass123!", nickname="test_user", is_active=True
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123!", nickname="admin_user", role="admin"
    )


@pytest.fixture
def dashboard_summary(db):
    return DashboardSummary.objects.create(
        total_orders=100,
        pending_orders=30,
        completed_orders=70,
        total_revenue=Decimal("1000.00"),
        new_users_today=5,
        active_chat_rooms=10,
        unresolved_cs_posts=3,
    )


@pytest.fixture
def authenticate_client(api_client):
    def _authenticate_client(user):
        api_client.force_authenticate(user=user)
        return user

    return _authenticate_client


@pytest.mark.django_db
class TestDashboardSummary:
    def test_create_dashboard_summary(self, user):
        """DashboardSummary 모델 생성 테스트"""
        summary = DashboardSummary.objects.create(
            user=user,
            total_orders=50,
            pending_orders=20,
            completed_orders=30,
            total_revenue=Decimal("500.00"),
            new_users_today=3,
            active_chat_rooms=5,
            unresolved_cs_posts=2,
        )

        assert summary.user == user
        assert summary.total_orders == 50
        assert summary.pending_orders == 20
        assert summary.completed_orders == 30
        assert summary.total_revenue == Decimal("500.00")
        assert summary.new_users_today == 3
        assert summary.active_chat_rooms == 5
        assert summary.unresolved_cs_posts == 2
        assert summary.last_updated is not None

    def test_dashboard_summary_str_method(self, user):
        """DashboardSummary __str__ 메서드 테스트"""
        summary = DashboardSummary.objects.create(user=user)
        assert str(summary) == f"Dashboard Summary for {user.email}"

        global_summary = DashboardSummary.objects.create()
        assert str(global_summary) == "Global Dashboard Summary"

    def test_list_dashboard_summary_as_admin(self, api_client, authenticate_client, admin_user, dashboard_summary):
        """관리자 권한으로 대시보드 요약 목록 조회"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("dashboard_summary:dashboard-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "대시보드 요약 정보 목록을 조회했습니다."
        assert "results" in response.data["data"], "Pagination이 적용되어 있어야 합니다"
        assert len(response.data["data"]["results"]) >= 1

    def test_list_dashboard_summary_as_normal_user(self, api_client, authenticate_client, user, dashboard_summary):
        """일반 사용자 권한으로 대시보드 요약 목록 조회"""
        authenticate_client(user)
        url = reverse("dashboard_summary:dashboard-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_global_dashboard_summary_as_admin(
        self, api_client, authenticate_client, admin_user, dashboard_summary
    ):
        """관리자 권한으로 전역 대시보드 요약 조회"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("dashboard_summary:dashboard-global")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["total_orders"] == dashboard_summary.total_orders
        assert response.data["message"] == "전역 대시보드 요약 정보를 조회했습니다."

    def test_retrieve_global_dashboard_summary_as_normal_user(
        self, api_client, authenticate_client, user, dashboard_summary
    ):
        """일반 사용자 권한으로 전역 대시보드 요약 조회 시도"""
        authenticate_client(user)
        url = reverse("dashboard_summary:dashboard-global")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_dashboard_detail_as_admin(self, api_client, authenticate_client, admin_user, dashboard_summary):
        """관리자 권한으로 특정 대시보드 요약 상세 조회"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("dashboard_summary:dashboard-detail", kwargs={"pk": dashboard_summary.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["total_orders"] == dashboard_summary.total_orders
        assert response.data["message"] == "전역 대시보드 요약 정보를 조회했습니다."

    def test_retrieve_dashboard_detail_as_normal_user(self, api_client, authenticate_client, user, dashboard_summary):
        """일반 사용자 권한으로 특정 대시보드 요약 상세 조회 시도"""
        authenticate_client(user)
        url = reverse("dashboard_summary:dashboard-detail", kwargs={"pk": dashboard_summary.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_revenue_calculation(self, db):
        """총 수익 계산 관련 테스트"""
        # 정상 케이스: max_digits=10, decimal_places=2 내의 값
        summary = DashboardSummary.objects.create(total_revenue=Decimal("999999.99"))
        assert summary.total_revenue == Decimal("999999.99")

        # 최대 자릿수 초과 테스트 - 유효성 검증으로 대체
        from django.core.exceptions import ValidationError

        large_summary = DashboardSummary(total_revenue=Decimal("99999999999.99"))  # 13자리로 max_digits(10) 초과
        with pytest.raises(ValidationError):
            large_summary.full_clean()
