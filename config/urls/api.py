"""API URL Configuration."""

from django.urls import include, path

urlpatterns = [
    path("analytics/", include("apps.analytics.urls", namespace="analytics")),
    path("user/", include("apps.user.urls", namespace="user")),
    path("cs-post/", include("apps.cs_post.urls", namespace="cs_post")),
    path("cs-reply/", include("apps.cs_reply.urls", namespace="cs_reply")),
    path("order/", include("apps.order.urls", namespace="order")),
    path("work/", include("apps.work.urls", namespace="work")),
    path("progress/", include("apps.progress.urls", namespace="progress")),
    path("preset-message/", include("apps.preset_message.urls", namespace="preset_message")),
    path("chat-room/", include("apps.chat_room.urls", namespace="chat_room")),
    path("chat-message/", include("apps.chat_message.urls", namespace="chat_message")),
    path("faq/", include("apps.faq.urls", namespace="faq")),
    path("notice/", include("apps.notice.urls", namespace="notice")),
    path("notification/", include("apps.notification.urls", namespace="notification")),
    path("dashboard-summary/", include("apps.dashboard_summary.urls", namespace="dashboard_summary")),
    path("order-status-log/", include("apps.order_status_log.urls", namespace="order_status_log")),
    path("like/", include("apps.like.urls", namespace="like")),
]
