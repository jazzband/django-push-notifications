from django.core.exceptions import ImproperlyConfigured
from django.utils.six import string_types
from .base import BaseConfig
from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


__all__ = [
	"LegacyConfig"
]


class empty(object):
	pass


class LegacyConfig(BaseConfig):
	def _get_application_settings(self, application_id, settings_key, error_message):
		"""Legacy behaviour"""

		if not application_id:
			value = SETTINGS.get(settings_key, empty)
			if value is empty:
				raise ImproperlyConfigured(error_message)
			return value
		else:
			msg = (
				"LegacySettings does not support application_id. To enable "
				"multiple application support, use push_notifications.conf.AppSettings."
			)
			raise ImproperlyConfigured(msg)

	def get_gcm_api_key(self, application_id=None):
		msg = (
			"Set PUSH_NOTIFICATIONS_SETTINGS[\"GCM_API_KEY\"] to send messages through GCM."
		)
		return self._get_application_settings(application_id, "GCM_API_KEY", msg)

	def get_fcm_api_key(self, application_id=None):
		msg = (
			"Set PUSH_NOTIFICATIONS_SETTINGS[\"FCM_API_KEY\"] to send messages through FCM."
		)
		return self._get_application_settings(application_id, "FCM_API_KEY", msg)

	def get_post_url(self, cloud_type, application_id=None):
		key = "{}_POST_URL".format(cloud_type)
		msg = (
			"Set PUSH_NOTIFICATIONS_SETTINGS[\"{}\"] to send messages through {}.".format(
				key, cloud_type
			)
		)
		return self._get_application_settings(application_id, key, msg)

	def get_error_timeout(self, cloud_type, application_id=None):
		key = "{}_ERROR_TIMEOUT".format(cloud_type)
		msg = (
			"Set PUSH_NOTIFICATIONS_SETTINGS[\"{}\"] to send messages through {}.".format(
				key, cloud_type
			)
		)
		return self._get_application_settings(application_id, key, msg)

	def get_max_recipients(self, cloud_type, application_id=None):
		key = "{}_MAX_RECIPIENTS".format(cloud_type)
		msg = (
			"Set PUSH_NOTIFICATIONS_SETTINGS[\"{}\"] to send messages through {}.".format(
				key, cloud_type
			)
		)
		return self._get_application_settings(application_id, key, msg)

	def get_apns_certificate(self, application_id=None):
		r = self._get_application_settings(
			application_id, "APNS_CERTIFICATE",
			"You need to setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		)
		if not isinstance(r, string_types):
			# probably the (Django) file, and file path should be got
			if hasattr(r, "path"):
				return r.path
			elif (hasattr(r, "has_key") or hasattr(r, "__contains__")) and "path" in r:
				return r["path"]
			else:
				msg = (
					"The APNS certificate settings value should be a string, or "
					"should have a 'path' attribute or key"
				)
				raise ImproperlyConfigured(msg)
		return r

	def get_apns_use_sandbox(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_USE_SANDBOX", msg)

	def get_apns_use_alternative_port(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_USE_ALTERNATIVE_PORT", msg)

	def get_apns_topic(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_TOPIC", msg)

	def get_apns_host(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_HOST", msg)

	def get_apns_port(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_PORT", msg)

	def get_apns_feedback_host(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_FEEDBACK_HOST", msg)

	def get_apns_feedback_port(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "APNS_FEEDBACK_PORT", msg)

	def get_wns_package_security_id(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WNS_PACKAGE_SECURITY_ID", msg)

	def get_wns_secret_key(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WNS_SECRET_KEY", msg)
