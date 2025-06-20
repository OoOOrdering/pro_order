from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import NotificationToken, UserNotificationSetting
from .serializers import NotificationTokenSerializer, UserNotificationSettingSerializer


class NotificationTokenRegisterView(generics.CreateAPIView):
    serializer_class = NotificationTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationTokenListView(generics.ListAPIView):
    serializer_class = NotificationTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationToken.objects.filter(user=self.request.user)


class NotificationTokenDeleteView(generics.DestroyAPIView):
    serializer_class = NotificationTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return NotificationToken.objects.filter(user=self.request.user)


class UserNotificationSettingView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationSettingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = UserNotificationSetting.objects.get_or_create(user=self.request.user)
        return obj
