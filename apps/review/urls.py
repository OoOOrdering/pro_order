from django.urls import path

from .views import ReviewDetailView, ReviewListCreateView

app_name = "review"

urlpatterns = [
    path("", ReviewListCreateView.as_view(), name="review-list-create"),
    path("<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
]
