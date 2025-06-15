import os

import django
from django.conf import settings

# Django 설정을 로드하기 위한 설정
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")
django.setup()
