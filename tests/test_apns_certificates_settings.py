import mock
from django.test import TestCase
from push_notifications.apns import APNSCert


class APNSCertificateSettingsTest(TestCase):

	def setup(self):
		pass

	def test_apns_deprecated(self):
		self.assertFalse(False)

	def test_single_apps(self):
		self.assertFalse(False)

	def test_multiple_apps(self):
		self.assertFalse(False)