from unittest import mock

from django.test import TestCase
from pywebpush import WebPushException

from push_notifications.exceptions import WebPushError
from push_notifications.webpush import (
	get_subscription_info, webpush_send_message
)

# Mock Responses
mock_success_response = mock.MagicMock(status_code=200, ok=True)
mock_fail_resposne = mock.MagicMock(status_code=400, ok=False, content="Test Error")
mock_unsubscribe_response = mock.MagicMock(
    status_code=410, ok=False, content="Unsubscribe")
mock_unsubscribe_response_404 = mock.MagicMock(
    status_code=404, ok=False, content="Unsubscribe")


class WebPushSendMessageTestCase(TestCase):
	def setUp(self):
		self.endpoint = "https://updates.push.services.mozilla.com/wpush/v2/token"
		self.mock_device = mock.Mock()
		self.mock_device.application_id = None
		self.mock_device.registration_id = self.endpoint
		self.mock_device.auth = "authtest"
		self.mock_device.p256dh = "p256dhtest"
		self.mock_device.active = True
		self.mock_device.save.return_value = True

	def test_get_subscription_info(self):
		keys = {"auth": "authtest", "p256dh": "p256dhtest"}
		endpoint = self.endpoint
		original = get_subscription_info(
			None, "token", "FIREFOX", keys["auth"], keys["p256dh"]
		)

		self.assertEqual(
			original,
			{
				"endpoint": endpoint,
				"keys": keys,
			},
		)

		patched = get_subscription_info(
			None,
			endpoint,
			"",
			keys["auth"],
			keys["p256dh"],
		)

		self.assertEqual(
			patched,
			{
				"endpoint": endpoint,
				"keys": keys,
			},
		)

	@mock.patch("push_notifications.webpush.webpush", return_value=mock_success_response)
	def test_webpush_send_message(self, webpush_mock):
		results = webpush_send_message(self.mock_device, "message")
		self.assertEqual(results["success"], 1)

	@mock.patch("push_notifications.webpush.webpush", return_value=mock_fail_resposne)
	def test_webpush_send_message_failure(self, webpush_mock):
		results = webpush_send_message(self.mock_device, "message")
		self.assertEqual(results["failure"], 1)

	@mock.patch(
        "push_notifications.webpush.webpush",
        side_effect=WebPushException("Unsubscribe",
        response=mock_unsubscribe_response))
	def test_webpush_send_message_unsubscribe(self, webpush_mock):
		results = webpush_send_message(self.mock_device, "message")
		self.assertEqual(results["failure"], 1)

	@mock.patch(
        "push_notifications.webpush.webpush",
        side_effect=WebPushException("Unsubscribe",
        response=mock_unsubscribe_response_404))
	def test_webpush_send_message_404(self, webpush_mock):
		results = webpush_send_message(self.mock_device, "message")
		self.assertEqual(results["failure"], 1)

	@mock.patch(
        "push_notifications.webpush.webpush",
        side_effect=WebPushException("Error"))
	def test_webpush_send_message_exception(self, webpush_mock):
		with self.assertRaises(WebPushError):
			webpush_send_message(self.mock_device, "message")
