from rest_framework import serializers

from .models import PresetMessage


class PresetMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresetMessage
        fields = "__all__"


class PresetMessageCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresetMessage
        fields = ("title", "content", "is_active")
