import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cedrus.settings")
django.setup()

print("Installed Apps:")
for app in settings.INSTALLED_APPS:
    print(f"- {app}")

from django.apps import apps

print("\nLoaded App Configs:")
for app_config in apps.get_app_configs():
    print(f"- {app_config.name} ({app_config.label})")
