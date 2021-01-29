from django.core.exceptions import ImproperlyConfigured

from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from .base import BaseConfig


__all__ = [
	"LegacyConfig"
]


class empty:
	pass


class LegacyConfig(BaseConfig):

	msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"

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
			'Set PUSH_NOTIFICATIONS_SETTINGS["GCM_API_KEY"] to send messages through GCM.'
		)
		return self._get_application_settings(application_id, "GCM_API_KEY", msg)

	def get_fcm_api_key(self, application_id=None):
		msg = (
			'Set PUSH_NOTIFICATIONS_SETTINGS["FCM_API_KEY"] to send messages through FCM.'
		)
		return self._get_application_settings(application_id, "FCM_API_KEY", msg)

	def get_post_url(self, cloud_type, application_id=None):
		key = "{}_POST_URL".format(cloud_type)
		msg = (
			'Set PUSH_NOTIFICATIONS_SETTINGS["{}"] to send messages through {}.'.format(
				key, cloud_type
			)
		)
		return self._get_application_settings(application_id, key, msg)

	def get_error_timeout(self, cloud_type, application_id=None):
		key = "{}_ERROR_TIMEOUT".format(cloud_type)
		msg = (
			'Set PUSH_NOTIFICATIONS_SETTINGS["{}"] to send messages through {}.'.format(
				key, cloud_type
			)
		)
		return self._get_application_settings(application_id, key, msg)

	def get_max_recipients(self, cloud_type, application_id=None):
		key = "{}_MAX_RECIPIENTS".format(cloud_type)
		msg = (
			'Set PUSH_NOTIFICATIONS_SETTINGS["{}"] to send messages through {}.'.format(
				key, cloud_type
			)
		)
		return self._get_application_settings(application_id, key, msg)

	def has_auth_token_creds(self, application_id=None):
		try:
			self._get_apns_auth_key(application_id)
			self._get_apns_auth_key_id(application_id)
			self._get_apns_team_id(application_id)
		except ImproperlyConfigured:
			return False

		return True

	def get_apns_certificate(self, application_id=None):
		r = self._get_application_settings(
			application_id, "APNS_CERTIFICATE",
			"You need to setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		)
		if not isinstance(r, str):
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

	def get_apns_auth_creds(self, application_id=None):
		return (
			self._get_apns_auth_key(application_id),
			self._get_apns_auth_key_id(application_id),
			self._get_apns_team_id(application_id))

	def _get_apns_auth_key(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_AUTH_KEY_PATH", self.msg)

	def _get_apns_team_id(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_TEAM_ID", self.msg)

	def _get_apns_auth_key_id(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_AUTH_KEY_ID", self.msg)

	def get_apns_use_sandbox(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_USE_SANDBOX", self.msg)

	def get_apns_use_alternative_port(self, application_id=None):
		return
		self._get_application_settings(application_id, "APNS_USE_ALTERNATIVE_PORT", self.msg)

	def get_apns_topic(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_TOPIC", self.msg)

	def get_apns_host(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_HOST", self.msg)

	def get_apns_port(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_PORT", self.msg)

	def get_apns_feedback_host(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_FEEDBACK_HOST", self.msg)

	def get_apns_feedback_port(self, application_id=None):
		return self._get_application_settings(application_id, "APNS_FEEDBACK_PORT", self.msg)

	def get_wns_package_security_id(self, application_id=None):
		return self._get_application_settings(application_id, "WNS_PACKAGE_SECURITY_ID", self.msg)

	def get_wns_secret_key(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WNS_SECRET_KEY", msg)

	def get_wp_post_url(self, application_id, browser):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WP_POST_URL", msg)[browser]

	def get_wp_private_key(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WP_PRIVATE_KEY", msg)

	def get_wp_claims(self, application_id=None):
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WP_CLAIMS", msg)
