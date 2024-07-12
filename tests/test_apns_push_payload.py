import sys
from unittest import mock

import pytest
from django.test import TestCase

try:
	from apns2.client import NotificationPriority
	from push_notifications.apns import _apns_send
	from push_notifications.exceptions import APNSUnsupportedPriority
except (AttributeError, ModuleNotFoundError):
	# skipping because apns2 is not supported on python 3.10
	# it uses hyper that imports from collections which were changed in 3.10
	# and we would get  "AttributeError: module 'collections' has no attribute 'MutableMapping'"
	if sys.version_info >= (3, 10):
		pytest.skip(allow_module_level=True)
	else:
		raise


class APNSPushPayloadTest(TestCase):

	def test_push_payload(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					_apns_send(
						"123", "Hello world", badge=1, sound="chime",
						extra={"custom_data": 12345}, expiration=3
					)

					self.assertTrue(s.called)
					args, kargs = s.call_args
					self.assertEqual(args[0], "123")
					self.assertEqual(args[1].alert, "Hello world")
					self.assertEqual(args[1].badge, 1)
					self.assertEqual(args[1].sound, "chime")
					self.assertEqual(args[1].custom, {"custom_data": 12345})
					self.assertEqual(kargs["expiration"], 3)

	def test_push_payload_with_thread_id(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					_apns_send(
						"123", "Hello world", thread_id="565", sound="chime",
						extra={"custom_data": 12345}, expiration=3
					)
				args, kargs = s.call_args
				self.assertEqual(args[0], "123")
				self.assertEqual(args[1].alert, "Hello world")
				self.assertEqual(args[1].thread_id, "565")
				self.assertEqual(args[1].sound, "chime")
				self.assertEqual(args[1].custom, {"custom_data": 12345})
				self.assertEqual(kargs["expiration"], 3)

	def test_push_payload_with_alert_dict(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					_apns_send(
						"123", alert={"title": "t1", "body": "b1"}, sound="chime",
						extra={"custom_data": 12345}, expiration=3
					)
					args, kargs = s.call_args
					self.assertEqual(args[0], "123")
					self.assertEqual(args[1].alert["body"], "b1")
					self.assertEqual(args[1].alert["title"], "t1")
					self.assertEqual(args[1].sound, "chime")
					self.assertEqual(args[1].custom, {"custom_data": 12345})
					self.assertEqual(kargs["expiration"], 3)

	def test_localised_push_with_empty_body(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					_apns_send("123", None, loc_key="TEST_LOC_KEY", expiration=3)
					args, kargs = s.call_args
					self.assertEqual(args[0], "123")
					self.assertEqual(args[1].alert.body_localized_key, "TEST_LOC_KEY")
					self.assertEqual(kargs["expiration"], 3)

	def test_using_extra(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					_apns_send(
						"123", "sample", extra={"foo": "bar"},
						expiration=30, priority=10
					)
					args, kargs = s.call_args
					self.assertEqual(args[0], "123")
					self.assertEqual(args[1].alert, "sample")
					self.assertEqual(args[1].custom, {"foo": "bar"})
					self.assertEqual(kargs["priority"], NotificationPriority.Immediate)
					self.assertEqual(kargs["expiration"], 30)

	def test_collapse_id(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					_apns_send(
						"123", "sample", collapse_id="456789"
					)
					args, kargs = s.call_args
					self.assertEqual(args[0], "123")
					self.assertEqual(args[1].alert, "sample")
					self.assertEqual(kargs["collapse_id"], "456789")

	def test_bad_priority(self):
		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					self.assertRaises(APNSUnsupportedPriority, _apns_send, "123", "_" * 2049, priority=24)
				s.assert_has_calls([])
