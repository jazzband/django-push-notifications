from unittest import mock

from django.test import TestCase

from push_notifications.gcm import send_bulk_message, send_message

from .responses import GCM_JSON, GCM_JSON_MULTIPLE


class GCMPushPayloadTest(TestCase):

	def test_fcm_push_payload(self):
		with mock.patch("push_notifications.gcm._fcm_send", return_value=GCM_JSON) as p:
			send_message("abc", {"message": "Hello world"}, "FCM")
			p.assert_called_once_with(
				b'{"notification":{"body":"Hello world"},"registration_ids":["abc"]}',
				"application/json", application_id=None)

	def test_push_payload_with_app_id(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_JSON) as p:
			send_message("abc", {"message": "Hello world"}, "GCM")
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"registration_ids":["abc"]}',
				"application/json", application_id=None)
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_JSON) as p:
			send_message("abc", {"message": "Hello world"}, "GCM")
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"registration_ids":["abc"]}',
				"application/json", application_id=None)

	def test_fcm_push_payload_params(self):
		with mock.patch("push_notifications.gcm._fcm_send", return_value=GCM_JSON) as p:
			send_message(
				"abc",
				{"message": "Hello world", "title": "Push notification", "other": "misc"},
				"FCM",
				delay_while_idle=True, time_to_live=3600, foo="bar",
			)
			p.assert_called_once_with(
				b'{"data":{"other":"misc"},"delay_while_idle":true,'
				b'"notification":{"body":"Hello world","title":"Push notification"},'
				b'"registration_ids":["abc"],"time_to_live":3600}',
				"application/json", application_id=None)

	def test_fcm_push_payload_many(self):
		with mock.patch("push_notifications.gcm._fcm_send", return_value=GCM_JSON_MULTIPLE) as p:
			send_bulk_message(["abc", "123"], {"message": "Hello world"}, "FCM")
			p.assert_called_once_with(
				b'{"notification":{"body":"Hello world"},"registration_ids":["abc","123"]}',
				"application/json", application_id=None)

	def test_gcm_push_payload(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_JSON) as p:
			send_message("abc", {"message": "Hello world"}, "GCM")
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"registration_ids":["abc"]}',
				"application/json", application_id=None)

	def test_gcm_push_payload_params(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_JSON) as p:
			send_message(
				"abc", {"message": "Hello world"}, "GCM",
				delay_while_idle=True, time_to_live=3600, foo="bar",
			)
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"delay_while_idle":true,'
				b'"registration_ids":["abc"],"time_to_live":3600}',
				"application/json", application_id=None)

	def test_gcm_push_payload_many(self):
		with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_JSON_MULTIPLE) as p:
			send_bulk_message(["abc", "123"], {"message": "Hello world"}, "GCM")
			p.assert_called_once_with(
				b'{"data":{"message":"Hello world"},"registration_ids":["abc","123"]}',
				"application/json",
				application_id=None)
