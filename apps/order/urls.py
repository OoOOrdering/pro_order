from django.urls import path

from .views import (
    OrderCancelView,
    OrderDetailView,
    OrderExportCSVView,
    OrderExportPDFView,
    OrderListCreateView,
    OrderRefundView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/refund/", OrderRefundView.as_view(), name="order-refund"),
    path("orders/export/csv/", OrderExportCSVView.as_view(), name="order-export-csv"),
    path(
        "orders/<int:pk>/export/pdf/",
        OrderExportPDFView.as_view(),
        name="order-export-pdf",
    ),
]
