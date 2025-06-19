import django_filters

from .models import PresetMessage


class PresetMessageFilter(django_filters.FilterSet):
    created_at = django_filters.DateFromToRangeFilter(field_name="created_at")
    updated_at = django_filters.DateFromToRangeFilter(field_name="updated_at")

    class Meta:
        model = PresetMessage
        fields = ["is_active", "user", "created_at", "updated_at"]
