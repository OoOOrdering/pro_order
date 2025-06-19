from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.user.models import User


class ChatRoom(models.Model):
    class RoomType(models.TextChoices):
        DIRECT = "DIRECT", _("1:1 채팅")
        GROUP = "GROUP", _("그룹 채팅")

    name = models.CharField(_("채팅방 이름"), max_length=100)
    description = models.TextField(_("채팅방 설명"), blank=True, null=True)
    max_participants = models.PositiveIntegerField(_("최대 참여자 수"), default=10)
    room_type = models.CharField(
        _("채팅방 유형"),
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.DIRECT,
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_rooms")
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    is_active = models.BooleanField(_("활성화 여부"), default=True)
    created_at = models.DateTimeField(_("생성일"), auto_now_add=True)
    updated_at = models.DateTimeField(_("수정일"), auto_now=True)
    last_message_at = models.DateTimeField(_("마지막 메시지 시간"), null=True, blank=True)

    class Meta:
        verbose_name = _("채팅방")
        verbose_name_plural = _("채팅방들")
        ordering = ["-last_message_at"]

    def __str__(self):
        return self.name


class ChatRoomParticipant(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="room_participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="room_participations")
    is_admin = models.BooleanField(_("관리자 여부"), default=False)
    joined_at = models.DateTimeField(_("참여일"), auto_now_add=True)
    left_at = models.DateTimeField(_("퇴장일"), null=True, blank=True)
    last_read_at = models.DateTimeField(_("마지막 읽은 시간"), null=True, blank=True)

    class Meta:
        verbose_name = _("채팅방 참여자")
        verbose_name_plural = _("채팅방 참여자들")
        unique_together = ("chat_room", "user")

    def __str__(self):
        return f"{self.user.email} - {self.chat_room.name}"
