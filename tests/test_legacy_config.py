from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from push_notifications.conf import LegacyConfig


class LegacyConfigTestCase(TestCase):
	def test_get_error_timeout(self):

		config = LegacyConfig()

		# confirm default value is None
		assert config.get_error_timeout("GCM") is None

		# confirm default value is None
		assert config.get_error_timeout("FCM") is None

		# confirm legacy does not support GCM with an application_id
		with self.assertRaises(ImproperlyConfigured) as ic:
			config.get_error_timeout("GCM", "my_app_id")

		self.assertEqual(
			str(ic.exception),
			"LegacySettings does not support application_id. To enable multiple"
			" application support, use push_notifications.conf.AppSettings."
		)

		# confirm legacy does not support FCM with an application_id
		with self.assertRaises(ImproperlyConfigured) as ic:
			config.get_error_timeout("FCM", "my_app_id")

		self.assertEqual(
			str(ic.exception),
			"LegacySettings does not support application_id. To enable multiple"
			" application support, use push_notifications.conf.AppSettings."
		)
