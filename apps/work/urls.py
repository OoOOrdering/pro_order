from django.urls import path

from .views import WorkDetailView, WorkListCreateView

urlpatterns = [
    path("works/", WorkListCreateView.as_view(), name="work-list-create"),
    path("works/<int:pk>/", WorkDetailView.as_view(), name="work-detail"),
]
