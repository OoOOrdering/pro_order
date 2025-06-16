from django.urls import path

from .views import ProgressDetailView, ProgressListCreateView

urlpatterns = [
    path("progresses/", ProgressListCreateView.as_view(), name="progress-list-create"),
    path("progresses/<int:pk>/", ProgressDetailView.as_view(), name="progress-detail"),
]
