from django.urls import path

from .views import NoticeDetailView, NoticeListCreateView

urlpatterns = [
    path("notices/", NoticeListCreateView.as_view(), name="notice-list-create"),
    path("notices/<int:pk>/", NoticeDetailView.as_view(), name="notice-detail"),
]
