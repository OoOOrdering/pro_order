from django.urls import path

from .views import ActionLogListView, ActionLogStatsView

urlpatterns = [
    path("", ActionLogListView.as_view(), name="action-log-list"),
    path("stats/", ActionLogStatsView.as_view(), name="action-log-stats"),
]
