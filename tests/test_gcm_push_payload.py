from django.test import TestCase
from push_notifications.gcm import send_message, send_bulk_message
from tests.test_models import GCM_PLAIN_RESPONSE, GCM_JSON_RESPONSE
from ._mock import mock


class GCMPushPayloadTest(TestCase):
	def test_push_payload(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
			send_message("abc", {"message": "Hello world"}, "GCM")
			p.assert_called_once_with(
				b"data.message=Hello+world&registration_id=abc",
				"application/x-www-form-urlencoded;charset=UTF-8")

	def test_push_payload_params(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
			send_message(
				"abc", {"message": "Hello world"}, "GCM", delay_while_idle=True, time_to_live=3600
			)
			p.assert_called_once_with(
				b"data.message=Hello+world&delay_while_idle=1&registration_id=abc&time_to_live=3600",
				"application/x-www-form-urlencoded;charset=UTF-8")

	def test_bulk_push_payload(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_JSON_RESPONSE) as p:
			send_bulk_message(["abc", "123"], {"message": "Hello world"}, "GCM")
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"registration_ids":["abc","123"]}',
				"application/json")
