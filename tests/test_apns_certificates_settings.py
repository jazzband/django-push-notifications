import warnings
import mock

from django.test import TestCase
from push_notifications import settings as SETTINGS
from push_notifications.apns import APNSCert


class APNSCertificateSettingsTest(TestCase):

	def setUp(self):
		self.pre_settings = SETTINGS.PUSH_NOTIFICATIONS_SETTINGS

	def tearDown(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS = self.pre_settings
	
	
	def test_apns_deprecated(self):
		SETTINGS.PUSH_NOTIFICATIONS_SETTINGS.update({
				"APNS_CERTIFICATE": "some/path/to/somewhere",
				"APNS_CA_CERTIFICATES": None

		})
		with warnings.catch_warnings(record=True) as w:
			warnings.simplefilter("always")
			wrapper = APNSCert()
			self.assertEquals(wrapper.certfile,
				SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"])
			self.assertIsNone(wrapper.ca_certs, 
				SETTINGS.PUSH_NOTIFICATIONS_SETTINGS["APNS_CA_CERTIFICATES"])
			self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
		

	def test_single_apps(self):
		self.assertFalse(False)

	def test_multiple_apps(self):
		self.assertFalse(False)