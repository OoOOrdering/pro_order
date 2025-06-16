import os

import django

# Django 설정을 로드하기 위한 설정
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")
django.setup()
