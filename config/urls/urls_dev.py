"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
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

from config.schema import schema_view  # 스웨거 설정 파일

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("apps.user.urls")),
    path("api/", include("apps.post.urls")),
    path(
        "api/posts/<int:post_id>/comments", include("apps.comment.urls")
    ),  # comment 앱의 URL
    path("api/", include("apps.like.urls")),
    path("api/", include("apps.idol.urls")),
    path("api/idols/", include("apps.follow.urls")),
    path("api/images/", include("apps.image.urls")),
    path("api/idols/", include("apps.idol_schedule.urls")),
    path("api/users/", include("apps.user_schedule.urls")),
    # path("api/", include("apps.notification.urls")),
    # path("api/", include("apps.notification_set.urls")),
    path(
        "swagger<format>", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# 개발 서버에서 미디어 파일을 서빙하기 위해 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
