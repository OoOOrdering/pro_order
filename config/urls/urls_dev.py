"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples
--------
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="PR Order API",
        default_version="v1",
        description="PR Order API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@prorder.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API URLs
    path("analytics/", include("apps.analytics.urls", namespace="analytics")),
    path("users/", include("apps.user.urls")),
    path("images/", include("apps.image.urls")),
    path("orders/", include("apps.order.urls")),
    path("order-status-logs/", include("apps.order_status_log.urls")),
    path("works/", include("apps.work.urls")),
    path("cs-posts/", include("apps.cs_post.urls")),
    path("cs-replies/", include("apps.cs_reply.urls")),
    path("chat-rooms/", include("apps.chat_room.urls")),
    path("chat-rooms/", include("apps.chat_message.urls")),  # chat_message 엔드포인트를 chat-rooms로 변경
    path("dashboard/", include("apps.dashboard_summary.urls")),
    path("faqs/", include("apps.faq.urls")),
    path("likes/", include("apps.like.urls")),
    path("notices/", include("apps.notice.urls")),
    path("notifications/", include("apps.notification.urls")),
    path("preset-messages/", include("apps.preset_message.urls")),
    path("progress/", include("apps.progress.urls")),
    path("reviews/", include("apps.review.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "swagger<format>/",
            schema_view.without_ui(cache_timeout=0),
            name="schema-json",
        ),
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "redoc/",
            schema_view.with_ui("redoc", cache_timeout=0),
            name="schema-redoc",
        ),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
