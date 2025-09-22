from django.core.exceptions import ImproperlyConfigured

from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from .base import BaseConfig
from typing import Any, Optional, Tuple


__all__ = [
	"LegacyConfig"
]


class empty:
	pass


class LegacyConfig(BaseConfig):
	msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"

	def _get_application_settings(self, application_id: Optional[str], settings_key: str, error_message: str) -> Any:
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

	def get_firebase_app(self, application_id: Optional[str] = None) -> Any:
		key = "FIREBASE_APP"
		msg = (
			'Set PUSH_NOTIFICATIONS_SETTINGS["{}"] to send messages through FCM.'.format(key)
		)
		return self._get_application_settings(application_id, key, msg)

	def get_max_recipients(self, application_id: Optional[str] = None) -> int:
		key = "FCM_MAX_RECIPIENTS"
		msg = (
			'Set PUSH_NOTIFICATIONS_SETTINGS["{}"] to send messages through FCM.'.format(key)
		)
		return self._get_application_settings(application_id, key, msg)

	def has_auth_token_creds(self, application_id: Optional[str] = None) -> bool:
		try:
			self._get_apns_auth_key(application_id)
			self._get_apns_auth_key_id(application_id)
			self._get_apns_team_id(application_id)
		except ImproperlyConfigured:
			return False

		return True

	def get_apns_certificate(self, application_id: Optional[str] = None) -> str:
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

	def get_apns_auth_creds(self, application_id: Optional[str] = None) -> Tuple[str, str, str]:
		return (
			self._get_apns_auth_key(application_id),
			self._get_apns_auth_key_id(application_id),
			self._get_apns_team_id(application_id))

	def _get_apns_auth_key(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "APNS_AUTH_KEY_PATH", self.msg)

	def _get_apns_team_id(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "APNS_TEAM_ID", self.msg)

	def _get_apns_auth_key_id(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "APNS_AUTH_KEY_ID", self.msg)

	def get_apns_use_sandbox(self, application_id: Optional[str] = None) -> bool:
		return self._get_application_settings(application_id, "APNS_USE_SANDBOX", self.msg)

	def get_apns_use_alternative_port(self, application_id: Optional[str] = None) -> bool:
		return self._get_application_settings(application_id, "APNS_USE_ALTERNATIVE_PORT", self.msg)

	def get_apns_topic(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "APNS_TOPIC", self.msg)

	def get_apns_host(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "APNS_HOST", self.msg)

	def get_apns_port(self, application_id: Optional[str] = None) -> int:
		return self._get_application_settings(application_id, "APNS_PORT", self.msg)

	def get_apns_feedback_host(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "APNS_FEEDBACK_HOST", self.msg)

	def get_apns_feedback_port(self, application_id: Optional[str] = None) -> int:
		return self._get_application_settings(application_id, "APNS_FEEDBACK_PORT", self.msg)

	def get_wns_package_security_id(self, application_id: Optional[str] = None) -> str:
		return self._get_application_settings(application_id, "WNS_PACKAGE_SECURITY_ID", self.msg)

	def get_wns_secret_key(self, application_id: Optional[str] = None) -> str:
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WNS_SECRET_KEY", msg)

	def get_wp_post_url(self, application_id: str, browser: str) -> str:
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WP_POST_URL", msg)[browser]

	def get_wp_private_key(self, application_id: Optional[str] = None) -> str:
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WP_PRIVATE_KEY", msg)

	def get_wp_claims(self, application_id: Optional[str] = None) -> dict:
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to send messages"
		return self._get_application_settings(application_id, "WP_CLAIMS", msg)

	def get_wp_error_timeout(self, application_id: Optional[str] = None) -> int:
		msg = "Setup PUSH_NOTIFICATIONS_SETTINGS properly to set a timeout"
		return self._get_application_settings(application_id, "WP_ERROR_TIMEOUT", msg)
