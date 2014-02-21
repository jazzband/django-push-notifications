from django.conf import settings

PUSH_NOTIFICATIONS_SETTINGS = getattr(settings, "PUSH_NOTIFICATIONS_SETTINGS", {})


# GCM
PUSH_NOTIFICATIONS_SETTINGS.setdefault("GCM_POST_URL", "https://android.googleapis.com/gcm/send")
PUSH_NOTIFICATIONS_SETTINGS.setdefault("GCM_MAX_RECIPIENTS", 1000)


# APNS
PUSH_NOTIFICATIONS_SETTINGS.setdefault("APNS_PORT", 2195)
if settings.DEBUG:
    PUSH_NOTIFICATIONS_SETTINGS.setdefault("APNS_HOST", "gateway.sandbox.push.apple.com")
else:
    PUSH_NOTIFICATIONS_SETTINGS.setdefault("APNS_HOST", "gateway.push.apple.com")
