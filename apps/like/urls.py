from django.urls import path

from .views import LikeDestroyView, LikeListCreateView

urlpatterns = [
    path("likes/", LikeListCreateView.as_view(), name="like-list-create"),
    path("likes/<int:pk>/", LikeDestroyView.as_view(), name="like-destroy"),
]
