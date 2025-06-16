from django.urls import path

from .views import OrderStatusLogDetailView, OrderStatusLogListCreateView

urlpatterns = [
    path(
        "order-status-logs/",
        OrderStatusLogListCreateView.as_view(),
        name="order-status-log-list-create",
    ),
    path(
        "order-status-logs/<int:pk>/",
        OrderStatusLogDetailView.as_view(),
        name="order-status-log-detail",
    ),
]
