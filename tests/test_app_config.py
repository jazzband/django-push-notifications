import os

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from push_notifications.conf import AppConfig


class AppConfigTestCase(TestCase):
	def test_application_id_required(self):
		"""Using AppConfig without an application_id raises ImproperlyConfigured."""

		manager = AppConfig()
		with self.assertRaises(ImproperlyConfigured):
			manager._get_application_settings(None, None, None)

	def test_application_not_found(self):
		"""
		Using AppConfig with an application_id that does not exist raises
		ImproperlyConfigured.
		"""

		application_id = "my_fcm_app"

		manager = AppConfig()

		with self.assertRaises(ImproperlyConfigured):
			manager._get_application_settings(application_id, "FCM", "API_KEY")

	def test_platform_configured(self):
		"""
		Using AppConfig with an application config that does not define PLATFORM
		raises ImproperlyConfigured.
		"""

		application_id = "my_fcm_app"
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				application_id: {}
			}
		}

		with self.assertRaises(ImproperlyConfigured):
			AppConfig(PUSH_SETTINGS)

	def test_platform_invalid(self):
		"""
		Using AppConfig with an invalid platform raises ImproperlyConfigured.
		"""

		application_id = "my_fcm_app"
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				application_id: {
					"PLATFORM": "XXX"
				}
			}
		}

		with self.assertRaises(ImproperlyConfigured):
			AppConfig(PUSH_SETTINGS)

	def test_platform_invalid_setting(self):
		"""
		Fetching application settings for the wrong platform raises ImproperlyConfigured.
		"""

		application_id = "my_fcm_app"
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				application_id: {
					"PLATFORM": "FCM",
					"API_KEY": "[my_api_key]"
				}
			}
		}

		manager = AppConfig(PUSH_SETTINGS)

		with self.assertRaises(ImproperlyConfigured):
			manager._get_application_settings(application_id, "APNS", "CERTIFICATE")

	def test_missing_setting(self):
		"""
		Missing application settings raises ImproperlyConfigured.
		"""

		application_id = "my_fcm_app"
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				application_id: {
					"PLATFORM": "FCM"
				}
			}
		}

		with self.assertRaises(ImproperlyConfigured):
			AppConfig(PUSH_SETTINGS)

	def test_validate_apns_config(self):
		"""
		Verify the settings for APNS platform.
		"""

		path = os.path.join(os.path.dirname(__file__), "test_data", "good_revoked.pem")

		#
		# all settings specified, required and optional, does not raise an error.
		#
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_apns_app": {
					"PLATFORM": "APNS",
					"CERTIFICATE": path,
					"USE_ALTERNATIVE_PORT": True,
					"USE_SANDBOX": True
				}
			}
		}
		AppConfig(PUSH_SETTINGS)

		# missing required settings
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_apns_app": {
					"PLATFORM": "APNS",
				}
			}
		}

		with self.assertRaises(ImproperlyConfigured) as ic:
			AppConfig(PUSH_SETTINGS)

		self.assertEqual(
			str(ic.exception),
			("PUSH_NOTIFICATIONS_SETTINGS.APPLICATIONS[\"my_apns_app\"][\"('CERTIFICATE', ['AUTH_KEY_PATH', 'AUTH_KEY_ID', 'TEAM_ID'])\"] is missing.")
		)

		#
		# certificate settings, with optional settings having default values
		#
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_apns_app": {
					"PLATFORM": "APNS",
					"CERTIFICATE": path,
				}
			}
		}

		manager = AppConfig(PUSH_SETTINGS)
		app_config = manager._settings["APPLICATIONS"]["my_apns_app"]

		assert app_config["USE_SANDBOX"] is False
		assert app_config["USE_ALTERNATIVE_PORT"] is False

		# certificate settings, with optional settings having default values
		#
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_apns_app": {
					"PLATFORM": "APNS",
					"AUTH_KEY_PATH": path,
					"AUTH_KEY_ID": "123456",
					"TEAM_ID": "123456",
				}
			}
		}

		manager = AppConfig(PUSH_SETTINGS)
		app_config = manager._settings["APPLICATIONS"]["my_apns_app"]

		assert app_config["USE_SANDBOX"] is False
		assert app_config["USE_ALTERNATIVE_PORT"] is False

	def test_get_allowed_settings_fcm(self):
		"""Verify the settings allowed for FCM platform."""

		#
		# all settings specified, required and optional, does not raise an error.
		#
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_fcm_app": {
					"PLATFORM": "FCM",
					"API_KEY": "...",
					"POST_URL": "...",
					"MAX_RECIPIENTS": "...",
					"ERROR_TIMEOUT": "...",
				}
			}
		}
		AppConfig(PUSH_SETTINGS)

		# missing required settings
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_fcm_app": {
					"PLATFORM": "FCM",
				}
			}
		}

		with self.assertRaises(ImproperlyConfigured):
			AppConfig(PUSH_SETTINGS)

		# all optional settings have default values
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_fcm_app": {
					"PLATFORM": "FCM",
					"API_KEY": "...",
				}
			}
		}

		manager = AppConfig(PUSH_SETTINGS)
		app_config = manager._settings["APPLICATIONS"]["my_fcm_app"]

		assert app_config["POST_URL"] == "https://fcm.googleapis.com/fcm/send"
		assert app_config["MAX_RECIPIENTS"] == 1000
		assert app_config["ERROR_TIMEOUT"] is None

	def test_get_allowed_settings_gcm(self):
		"""Verify the settings allowed for GCM platform."""

		#
		# all settings specified, required and optional, does not raise an error.
		#
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_gcm_app": {
					"PLATFORM": "GCM",
					"API_KEY": "...",
					"POST_URL": "...",
					"MAX_RECIPIENTS": "...",
					"ERROR_TIMEOUT": "...",
				}
			}
		}
		AppConfig(PUSH_SETTINGS)

		#
		# missing required settings
		#
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_gcm_app": {
					"PLATFORM": "GCM",
				}
			}
		}

		with self.assertRaises(ImproperlyConfigured):
			AppConfig(PUSH_SETTINGS)

		# all optional settings have default values
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_gcm_app": {
					"PLATFORM": "GCM",
					"API_KEY": "...",
				}
			}
		}

		manager = AppConfig(PUSH_SETTINGS)
		app_config = manager._settings["APPLICATIONS"]["my_gcm_app"]

		assert app_config["POST_URL"] == "https://android.googleapis.com/gcm/send"
		assert app_config["MAX_RECIPIENTS"] == 1000
		assert app_config["ERROR_TIMEOUT"] is None

	def test_get_allowed_settings_wns(self):
		"""
		Verify the settings allowed for WNS platform.
		"""

		# all settings specified, required and optional, does not raise an error.
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_wns_app": {
					"PLATFORM": "WNS",
					"PACKAGE_SECURITY_ID": "...",
					"SECRET_KEY": "...",
					"WNS_ACCESS_URL": "...",
				}
			}
		}
		AppConfig(PUSH_SETTINGS)

		# missing required settings
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_wns_app": {
					"PLATFORM": "WNS",
				}
			}
		}

		with self.assertRaises(ImproperlyConfigured):
			AppConfig(PUSH_SETTINGS)

		# all optional settings have default values
		PUSH_SETTINGS = {
			"APPLICATIONS": {
				"my_wns_app": {
					"PLATFORM": "WNS",
					"PACKAGE_SECURITY_ID": "...",
					"SECRET_KEY": "...",
				}
			}
		}

		manager = AppConfig(PUSH_SETTINGS)
		app_config = manager._settings["APPLICATIONS"]["my_wns_app"]

		assert app_config["WNS_ACCESS_URL"] == "https://login.live.com/accesstoken.srf"
