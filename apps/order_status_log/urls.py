from django.urls import path

from .views import OrderStatusLogDetailView, OrderStatusLogListCreateView

app_name = "order_status_log"

urlpatterns = [
    path(
        "",
        OrderStatusLogListCreateView.as_view(),
        name="order-status-log-list-create",
    ),
    path(
        "<int:pk>/",
        OrderStatusLogDetailView.as_view(),
        name="order-status-log-detail",
    ),
]
