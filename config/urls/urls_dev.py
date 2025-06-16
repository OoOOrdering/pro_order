"""URL configuration for config project.

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
    path("admin/", admin.site.urls),
    path("api/users/", include("apps.user.urls")),
    path("api/images/", include("apps.image.urls")),
    path("api/orders/", include("apps.order.urls")),
    path("api/order-status-logs/", include("apps.order_status_log.urls")),
    path("api/works/", include("apps.work.urls")),
    path("api/chat-rooms/", include("apps.chat_room.urls")),
    path("api/chat-messages/", include("apps.chat_message.urls")),
    path("api/notices/", include("apps.notice.urls")),
    path("api/reviews/", include("apps.review.urls")),
    path("api/preset-messages/", include("apps.preset_message.urls")),
    path("api/faqs/", include("apps.faq.urls")),
    path("api/cs_posts/", include("apps.cs_post.urls")),
    path("api/cs_replies/", include("apps.cs_reply.urls")),
    path("api/notifications/", include("apps.notification.urls")),
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
