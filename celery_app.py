import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")

app = Celery("pr_order")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# 예시 태스크
def debug_task():
    print("Celery debug task executed!")


app.task(debug_task)
