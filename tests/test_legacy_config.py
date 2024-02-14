from unittest import mock

from django.test import TestCase

from push_notifications.conf import get_manager
from push_notifications.exceptions import WebPushError
from push_notifications.webpush import webpush_send_message


class LegacyConfigTestCase(TestCase):

	def test_immutable_wp_claims(self):
		self.endpoint = "https://updates.push.services.mozilla.com/wpush/v2/token"
		self.mock_device = mock.Mock()
		self.mock_device.application_id = None
		self.mock_device.registration_id = self.endpoint
		self.mock_device.auth = "authtest"
		self.mock_device.p256dh = "p256dhtest"
		self.mock_device.active = True
		self.mock_device.save.return_value = True
		vapid_claims_pre = get_manager().get_wp_claims(None).copy()
		try:
			webpush_send_message(self.mock_device, "message")
		except WebPushError:
			pass
		vapid_claims_after = get_manager().get_wp_claims(None)
		self.assertDictEqual(vapid_claims_pre, vapid_claims_after)
