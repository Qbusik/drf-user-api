import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "drf_user_api.settings")

app = Celery("drf_user_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
