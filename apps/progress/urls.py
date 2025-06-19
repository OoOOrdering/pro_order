from django.urls import path

from .views import ProgressDetailView, ProgressListCreateView

app_name = "progress"

urlpatterns = [
    path("", ProgressListCreateView.as_view(), name="progress-list-create"),
    path("<int:pk>/", ProgressDetailView.as_view(), name="progress-detail"),
]
