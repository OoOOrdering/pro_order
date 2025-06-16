from django.urls import path

from .views import ReviewDetailView, ReviewListCreateView

urlpatterns = [
    path("reviews/", ReviewListCreateView.as_view(), name="review-list-create"),
    path("reviews/<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
]
