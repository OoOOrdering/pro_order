from django.urls import path

from .views import (
    MarkNotificationAsReadView,
    NotificationDetailView,
    NotificationListCreateView,
    NotificationUnreadCountView,
    UnreadNotificationListView,
)

urlpatterns = [
    path(
        "notifications/",
        NotificationListCreateView.as_view(),
        name="notification-list-create",
    ),
    path(
        "notifications/<int:pk>/",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "notifications/unread/",
        UnreadNotificationListView.as_view(),
        name="notification-unread-list",
    ),
    path(
        "notifications/<int:pk>/mark-as-read/",
        MarkNotificationAsReadView.as_view(),
        name="notification-mark-as-read",
    ),
    path(
        "notifications/unread_count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
]
