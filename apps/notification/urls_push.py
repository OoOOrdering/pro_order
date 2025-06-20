from django.urls import path

from .views_push import (
    NotificationTokenDeleteView,
    NotificationTokenListView,
    NotificationTokenRegisterView,
    UserNotificationSettingView,
)

urlpatterns = [
    path("push/token/", NotificationTokenRegisterView.as_view(), name="notification-token-register"),
    path("push/tokens/", NotificationTokenListView.as_view(), name="notification-token-list"),
    path("push/token/<int:pk>/", NotificationTokenDeleteView.as_view(), name="notification-token-delete"),
    path("push/setting/", UserNotificationSettingView.as_view(), name="notification-setting"),
]
