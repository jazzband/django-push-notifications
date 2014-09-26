import mock
import json
from django.test import TestCase
from push_notifications.gcm import gcm_send_message, gcm_send_bulk_message


class GCMPushPayloadTest(TestCase):
	def test_push_payload(self):
		with mock.patch("push_notifications.gcm._gcm_send") as p:
			gcm_send_message("abc", {"message": "Hello world"})
			p.assert_called_once_with(
				b"registration_id=abc&data.message=Hello+world",
				"application/x-www-form-urlencoded;charset=UTF-8")

	def test_push_nested_payload(self):
		with mock.patch("push_notifications.gcm._gcm_send") as p:
			payload = {
				"message": "Hello world",
				"extra": {
					"key0": ["value0_0", "value0_1", "value0_2"],
					"key1": "value1",
					"key2": {"key2_0": "value2_0"}
				}
			}
			payload_string = json.dumps(payload, separators=(",", ":")).encode("utf-8")
			gcm_send_message("abc", payload)
			p.assert_called_once_with(
				b'{"data":' + payload_string + b',"registration_ids":["abc"]}',
				"application/json")

	def test_bulk_push_payload(self):
		with mock.patch("push_notifications.gcm._gcm_send") as p:
			gcm_send_bulk_message(["abc", "123"], {"message": "Hello world"})
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"registration_ids":["abc","123"]}',
				"application/json")
