import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:
    def __init__(
        self,
        min_length=12,
        require_upper=True,
        require_lower=True,
        require_digit=True,
        require_special=True,
    ):
        self.min_length = min_length
        self.require_upper = require_upper
        self.require_lower = require_lower
        self.require_digit = require_digit
        self.require_special = require_special

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("비밀번호는 최소 %(min_length)d자 이상이어야 합니다."),
                code="password_too_short",
                params={"min_length": self.min_length},
            )

        if self.require_upper and not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("비밀번호는 하나 이상의 대문자를 포함해야 합니다."),
                code="password_no_upper",
            )

        if self.require_lower and not re.search(r"[a-z]", password):
            raise ValidationError(
                _("비밀번호는 하나 이상의 소문자를 포함해야 합니다."),
                code="password_no_lower",
            )

        if self.require_digit and not re.search(r"\d", password):
            raise ValidationError(
                _("비밀번호는 하나 이상의 숫자를 포함해야 합니다."),
                code="password_no_digit",
            )

        if self.require_special and not re.search(r"[^\w\s]", password):
            raise ValidationError(
                _("비밀번호는 하나 이상의 특수 문자를 포함해야 합니다."),
                code="password_no_special",
            )

    def get_help_text(self):
        help_text = _("비밀번호는 최소 %(min_length)d자 이상이어야 합니다. ") % {"min_length": self.min_length}
        if self.require_upper:
            help_text += _("하나 이상의 대문자, ")
        if self.require_lower:
            help_text += _("하나 이상의 소문자, ")
        if self.require_digit:
            help_text += _("하나 이상의 숫자, ")
        if self.require_special:
            help_text += _("하나 이상의 특수 문자를 포함해야 합니다.")

        # Remove trailing comma and space if any
        if help_text.endswith(", "):
            help_text = help_text[:-2] + "."
        return help_text
