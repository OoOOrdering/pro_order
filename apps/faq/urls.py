from django.urls import path

from .views import FAQDetailView, FAQListCreateView, PublishedFAQListView

urlpatterns = [
    path("faqs/", FAQListCreateView.as_view(), name="faq-list-create"),
    path("faqs/<int:pk>/", FAQDetailView.as_view(), name="faq-detail"),
    path("faqs/published/", PublishedFAQListView.as_view(), name="faq-published-list"),
]
