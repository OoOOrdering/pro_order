from django.urls import path

from .views import CSReplyDetailView, CSReplyListCreateView

urlpatterns = [
    path(
        "cs-posts/<int:cs_post_pk>/replies/",
        CSReplyListCreateView.as_view(),
        name="cs-reply-list-create",
    ),
    path(
        "cs-posts/<int:cs_post_pk>/replies/<int:pk>/",
        CSReplyDetailView.as_view(),
        name="cs-reply-detail",
    ),
]
