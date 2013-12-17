from django.conf import settings

__author__ = "Jerome Leclanche"
__email__ = "jerome.leclanche+pypi@gmail.com"
__version__ = "0.8"


PUSH_NOTIFICATIONS_SETTINGS = getattr(settings, "PUSH_NOTIFICATIONS_SETTINGS", {})


class NotificationError(Exception):
	pass
