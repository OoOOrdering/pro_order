from django.urls import path

from .views import DailyAnalyticsListView, EventLogDetailView, EventLogListCreateView

urlpatterns = [
    path(
        "daily-analytics/",
        DailyAnalyticsListView.as_view(),
        name="daily-analytics-list",
    ),
    path("event-logs/", EventLogListCreateView.as_view(), name="event-log-list-create"),
    path("event-logs/<int:pk>/", EventLogDetailView.as_view(), name="event-log-detail"),
]
