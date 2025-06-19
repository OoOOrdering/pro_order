from django.urls import path

from .views import DashboardSummaryListView, DashboardSummaryView

app_name = "dashboard_summary"

urlpatterns = [
    path("", DashboardSummaryListView.as_view(), name="dashboard-list"),
    path("global/", DashboardSummaryView.as_view(), name="dashboard-global"),
    path("<int:pk>/", DashboardSummaryView.as_view(), name="dashboard-detail"),
]
