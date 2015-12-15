import warnings
import mock

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from push_notifications import settings as SETTINGS
from push_notifications.apns import APNSCert
from push_notifications import checks


class APNSCertificateSettingsTest(TestCase):

	def tearDown(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_CERTIFICATE", None)
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_CA_CERTIFICATES", None)
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_APP_CERTIFICATES", None)

	def test_old_apns_certificate_check(self):
		"""Force the user to upgrade to the new certificate settings format."""

		# confirm check if APNS_CERTIFICATE is set
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] = "/dev/null"
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CA_CERTIFICATES"] =  None
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_APP_CERTIFICATES", None)

		errors = checks.check_apns_settings()
		self.assertEqual(1, len(errors))
		self.assertEqual(errors[0].id, "django_push_notifications.W001")

		# confirm check is not raised if APNS_CERTIFICATE is not set
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_CERTIFICATE", None)

		errors = checks.check_apns_settings()
		self.assertEqual(0, len(errors))

	def test_apns_app_certificates_check(self):
		"""Validate system checks for APNS_APP_CERTIFICATES setting."""

		# django_push_notifications.C003 - at least one app defined
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {}

		errors = checks.check_apns_settings()
		self.assertEqual(1, len(errors))
		self.assertEqual(errors[0].id, "django_push_notifications.E001")

		# django_push_notifications.C004 - APNS_CERTIFICATE define for app
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {
			"app": {}
		}

		errors = checks.check_apns_settings()
		self.assertEqual(1, len(errors))
		self.assertEqual(errors[0].id, "django_push_notifications.E002")

		# django_push_notifications.C005 - APNS_CERTIFICATE is readable
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {
			"app": {
				"APNS_CERTIFICATE": "/tmp/doesnotexist"  # not readable
			}
		}

		errors = checks.check_apns_settings()
		self.assertEqual(1, len(errors))
		self.assertEqual(errors[0].id, "django_push_notifications.E003")

		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {
			"app": {
				"APNS_CERTIFICATE": "/dev/null"  # readable
			}
		}

		errors = checks.check_apns_settings()
		self.assertEqual(0, len(errors))

	def test_single_apps(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {
					"App1": {
						"APNS_CERTIFICATE": "/dev/null",
						"APNS_CA_CERTIFICATES": "/dev/null"
					}
		}
		wrapper = APNSCert()
		app1 = SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"]["App1"]
		self.assertEquals(wrapper.cert, app1["APNS_CERTIFICATE"])
		self.assertEquals(wrapper.ca_cert, app1["APNS_CA_CERTIFICATES"])

		with self.assertRaises(ImproperlyConfigured):
			SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {}
			APNSCert()
		with self.assertRaises(ImproperlyConfigured):
			SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_APP_CERTIFICATES", None)
			APNSCert()

	def test_multiple_apps(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"] = {
					"App1": {
						"APNS_CERTIFICATE": "/dev/null",
						"APNS_CA_CERTIFICATES": None
					},
					"App2": {
						"APNS_CERTIFICATE": "/dev/null",
						"APNS_CA_CERTIFICATES": None
					}
		}
		wrapper = APNSCert(app_name="App2")
		app1 = SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_APP_CERTIFICATES"]["App2"]
		self.assertEquals(wrapper.cert, app1["APNS_CERTIFICATE"])
		self.assertIsNone(wrapper.ca_cert, app1["APNS_CA_CERTIFICATES"])
		with self.assertRaises(ValueError):
			APNSCert(app_name="Bogus")
