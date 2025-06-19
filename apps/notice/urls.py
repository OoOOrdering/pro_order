from django.urls import path

from .views import NoticeDetailView, NoticeListCreateView, RecentNoticeListView

app_name = "notice"

urlpatterns = [
    path("notices/recent/", RecentNoticeListView.as_view(), name="recent-notice-list"),
    path("notices/<int:pk>/", NoticeDetailView.as_view(), name="notice-detail"),
    path("notices/", NoticeListCreateView.as_view(), name="notice-list-create"),
]
