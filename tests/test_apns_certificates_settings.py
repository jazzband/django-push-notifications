import warnings
import mock

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from push_notifications import settings as SETTINGS
from push_notifications.apns import APNSCert


class APNSCertificateSettingsTest(TestCase):

	def tearDown(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_CERTIFICATE", None)
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_CA_CERTIFICATES", None)
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.pop("APNS_APP_CERTIFICATES", None)
	
	def test_apns_deprecated(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] = "/dev/null"
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CA_CERTIFICATES"] =  None
		with warnings.catch_warnings(record=True) as w:
			warnings.simplefilter("always")
			wrapper = APNSCert()
			self.assertEquals(wrapper.cert,
				SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"])
			self.assertIsNone(wrapper.ca_cert, 
				SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CA_CERTIFICATES"])
			self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
		

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
			APNSCert(app_name='Bogus')
