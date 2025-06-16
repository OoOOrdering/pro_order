from django.db import models

from apps.order.models import Order
from apps.user.models import User


class Review(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name="주문",
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="리뷰어",
    )
    rating = models.PositiveIntegerField(
        choices=(
            (1, "1 Star"),
            (2, "2 Stars"),
            (3, "3 Stars"),
            (4, "4 Stars"),
            (5, "5 Stars"),
        ),
        verbose_name="평점",
    )
    comment = models.TextField(blank=True, null=True, verbose_name="리뷰 내용")
    is_public = models.BooleanField(default=True, verbose_name="공개 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")
    image = models.ImageField(upload_to="reviews/", blank=True, null=True)
    is_best = models.BooleanField(default=False)
    reported = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review for Order {self.order.order_number if self.order else 'N/A'} by {self.reviewer.username}"


class ReviewReport(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
