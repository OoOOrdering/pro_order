import json
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from .models import DailyAnalytics, EventLog


@pytest.fixture
def daily_analytics():
    return DailyAnalytics.objects.create(
        date=date.today(),
        page_views=100,
        unique_visitors=50,
        conversion_rate=Decimal("2.5"),
        average_order_value=Decimal("75.50"),
    )


@pytest.fixture
def event_log(admin_user):
    return EventLog.objects.create(
        user=admin_user,
        event_name="테스트 이벤트",
        event_type=EventLog.EventType.PAGE_VIEW,
        value=1.0,
        object_id="1",
        object_type="test",
        metadata={"test": "data"},
    )


@pytest.mark.django_db
class TestDailyAnalytics:
    def test_daily_analytics_str(self, daily_analytics):
        """DailyAnalytics 모델의 __str__ 메서드를 테스트합니다."""
        assert str(daily_analytics) == f"일별 분석: {daily_analytics.date}"

    def test_get_daily_analytics_list_admin(self, authenticated_client, daily_analytics):
        """관리자 사용자의 일별 분석 목록 조회를 테스트합니다."""
        client, user = authenticated_client(is_staff=True)
        url = reverse("analytics:daily-analytics-list")
        response = client.get(url)

        assert response.status_code == 200
        data = response.data
        assert isinstance(data, dict)
        assert "results" in data
        analytics = data["results"][0]
        assert analytics["date"] == daily_analytics.date.isoformat()
        assert analytics["page_views"] == daily_analytics.page_views
        assert analytics["unique_visitors"] == daily_analytics.unique_visitors
        # 소수점 자리수 포맷을 맞춰서 비교
        assert float(analytics["conversion_rate"]) == float(daily_analytics.conversion_rate)
        assert float(analytics["average_order_value"]) == float(daily_analytics.average_order_value)

    def test_get_daily_analytics_list_non_admin(self, authenticated_client, daily_analytics):
        """일반 사용자의 일별 분석 목록 조회 시도를 테스트합니다."""
        client, _ = authenticated_client(is_staff=False)
        url = reverse("analytics:daily-analytics-list")
        response = client.get(url)
        assert response.status_code == 403

    def test_filter_daily_analytics_by_date(self, authenticated_client, daily_analytics):
        """날짜 필터링을 테스트합니다."""
        client, _ = authenticated_client(is_staff=True)
        url = reverse("analytics:daily-analytics-list")

        # 시작 날짜와 종료 날짜로 필터링
        start_date = (date.today() - timedelta(days=1)).isoformat()
        end_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.get(f"{url}?start_date={start_date}&end_date={end_date}")

        assert response.status_code == 200
        data = response.data
        assert isinstance(data, dict)
        assert "results" in data
        assert len(data["results"]) >= 1


@pytest.mark.django_db
class TestEventLog:
    def test_create_event_log(self, authenticated_client):
        """이벤트 로그 생성을 테스트합니다."""
        client, user = authenticated_client()
        url = reverse("analytics:event-log-list-create")
        data = {
            "event_name": "테스트 이벤트",
            "event_type": EventLog.EventType.PAGE_VIEW,
            "value": 1.0,
            "object_id": "1",
            "object_type": "test",
            "metadata": {"test": "data"},
        }
        response = client.post(url, data, format="json")
        assert response.status_code == 201
        assert response.data["success"] is True
        assert response.data["data"]["event_name"] == data["event_name"]
        assert response.data["data"]["event_type"] == data["event_type"]
        assert response.data["data"]["user"]["id"] == user.id

    def test_get_event_logs(self, authenticated_client, event_log):
        """이벤트 로그 목록 조회를 테스트합니다."""
        client, user = authenticated_client(is_staff=True)
        url = reverse("analytics:event-log-list-create")
        response = client.get(url)

        assert response.status_code == 200
        data = response.data
        assert isinstance(data, dict)
        assert "results" in data
        assert len(data["results"]) >= 1
        first_event = data["results"][0]
        assert "event_name" in first_event
        assert "event_type" in first_event
        assert "user" in first_event

    def test_filter_event_logs(self, authenticated_client, event_log):
        """이벤트 로그 필터링을 테스트합니다."""
        client, _ = authenticated_client(is_staff=True)
        url = reverse("analytics:event-log-list-create")

        # 이벤트 타입으로 필터링
        response = client.get(f"{url}?event_type={EventLog.EventType.PAGE_VIEW}")
        assert response.status_code == 200
        data = response.data
        assert isinstance(data, dict)
        assert "results" in data
        assert len(data["results"]) >= 1
        assert all(e["event_type"] == EventLog.EventType.PAGE_VIEW for e in data["results"])

    def test_search_event_logs(self, authenticated_client, event_log):
        """이벤트 로그 검색을 테스트합니다."""
        client, _ = authenticated_client(is_staff=True)
        url = reverse("analytics:event-log-list-create")

        # 이벤트 이름으로 검색
        response = client.get(f"{url}?search=테스트")
        assert response.status_code == 200
        data = response.data
        assert isinstance(data, dict)
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_non_admin_user_sees_only_own_events(self, authenticated_client, event_log):
        """일반 사용자가 자신의 이벤트만 볼 수 있는지 테스트합니다."""
        client, user = authenticated_client(is_staff=False)
        url = reverse("analytics:event-log-list-create")

        # 다른 사용자의 이벤트 생성
        own_event = EventLog.objects.create(
            user=user, event_name="자신의 이벤트", event_type=EventLog.EventType.PAGE_VIEW
        )

        response = client.get(url)
        assert response.status_code == 200
        data = response.data
        assert isinstance(data, dict)
        assert "results" in data
        # 자신의 이벤트만 보여야 함
        for event in data["results"]:
            assert event["user"]["id"] == user.id

    def test_get_event_log_detail_admin(self, authenticated_client, event_log):
        """관리자 사용자의 이벤트 로그 상세 조회를 테스트합니다."""
        client, _ = authenticated_client(is_staff=True)
        url = reverse("analytics:event-log-detail", kwargs={"pk": event_log.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == event_log.pk
        assert response.data["event_name"] == event_log.event_name
        assert response.data["event_type"] == event_log.event_type

    def test_get_event_log_detail_non_owner(self, authenticated_client, event_log):
        """일반 사용자가 다른 사용자의 이벤트 로그를 조회할 수 없음을 테스트합니다."""
        client, _ = authenticated_client(is_staff=False)
        url = reverse("analytics:event-log-detail", kwargs={"pk": event_log.pk})
        response = client.get(url)

        # 다른 사용자의 이벤트이므로 404를 반환해야 함
        assert response.status_code == 404

    def test_get_event_log_detail_owner(self, authenticated_client):
        """사용자가 자신의 이벤트 로그를 조회할 수 있음을 테스트합니다."""
        client, user = authenticated_client(is_staff=False)

        # 사용자의 이벤트 생성
        own_event = EventLog.objects.create(
            user=user, event_name="자신의 이벤트", event_type=EventLog.EventType.PAGE_VIEW
        )

        url = reverse("analytics:event-log-detail", kwargs={"pk": own_event.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == own_event.pk
        assert response.data["event_name"] == own_event.event_name
