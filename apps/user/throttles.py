from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import exception_handler


class LoginAttemptThrottle(AnonRateThrottle):
    scope = "login"
    rate = "5/minute"  # Default rate, can be overridden by settings

    def allow_request(self, request, view):
        if request.user.is_authenticated:
            return True

        ident = self.get_ident(request)
        self.key = self.cache_format % {"scope": self.scope, "ident": ident}

        # Get the number of failed attempts and last failed attempt time from cache
        failed_attempts = cache.get(f"login_failed_attempts_{ident}", 0)
        last_failed_attempt_time = cache.get(f"login_last_failed_attempt_time_{ident}")

        if failed_attempts >= settings.LOGIN_ATTEMPTS_LIMIT:
            if (
                last_failed_attempt_time
                and (datetime.now() - last_failed_attempt_time).total_seconds() < settings.LOGIN_LOCKOUT_TIME
            ):
                # Still locked out
                self.wait_time = (
                    settings.LOGIN_LOCKOUT_TIME - (datetime.now() - last_failed_attempt_time).total_seconds()
                )
                return False
            else:
                # Lockout period expired, reset attempts
                cache.delete(f"login_failed_attempts_{ident}")
                cache.delete(f"login_last_failed_attempt_time_{ident}")

        # Proceed with normal throttling check
        return super().allow_request(request, view)

    def wait(self):
        if hasattr(self, "wait_time"):
            return self.wait_time
        return super().wait()


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first, to get the standard error response.
    response = exception_handler(exc, context)

    # Handle Throttled exception specifically
    if isinstance(exc, status.HTTP_429_TOO_MANY_REQUESTS):
        wait_time = getattr(exc, "wait", None)
        detail = f"요청이 너무 많습니다. {int(wait_time)}초 후에 다시 시도해주세요." if wait_time else exc.detail
        response.data = {"detail": detail}

    return response
