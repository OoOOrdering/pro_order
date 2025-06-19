from typing import List, Union

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


def send_email(subject: str, message: str, to_email: Union[str, List[str]]) -> None:
    """
    이메일을 발송합니다.
    :param subject: 제목
    :param message: 본문
    :param to_email: 수신자 이메일(문자열 또는 리스트)
    :raises Exception: 발송 실패 시 예외 발생
    """
    to_email = to_email if isinstance(to_email, list) else [to_email]

    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, to_email)
    except Exception as e:
        print(repr(e))
        raise


@shared_task
def send_email_async(subject: str, message: str, to_email: Union[str, List[str]]) -> None:
    """
    Celery 비동기 태스크로 이메일을 발송합니다.
    """
    send_email(subject, message, to_email)
