from django.conf import settings

PUSH_NOTIFICATIONS_SETTINGS = getattr(settings, "PUSH_NOTIFICATIONS_SETTINGS", {})


class NotificationError(Exception):
	pass
