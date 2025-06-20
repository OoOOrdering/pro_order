from django.conf import settings
from django.db import models


class ActionLog(models.Model):
    ACTION_CHOICES = [
        ("login", "로그인"),
        ("order", "주문"),
        ("payment", "결제"),
        ("notification", "알림"),
        ("review", "리뷰"),
        ("chat", "채팅"),
        ("admin", "관리자 액션"),
        ("etc", "기타"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"
