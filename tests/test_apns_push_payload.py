import sys
from unittest import mock

import pytest
from django.test import TestCase


try:
	from apns2.client import NotificationPriority

	from push_notifications.apns import (
		_apns_prepare, _apns_send, apns_send_bulk_message, apns_send_message
	)
	from push_notifications.enums import InterruptionLevelType
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

	def test_interruption_level(self):
		cases = [
			(InterruptionLevelType.ACTIVE, "active"),
			(InterruptionLevelType.PASSIVE, "passive"),
			(InterruptionLevelType.TIME_SENSITIVE, "time-sensitive"),
			(InterruptionLevelType.CRITICAL, "critical"),
			("time-sensitive", "time-sensitive"),
			("passive", "passive"),
		]
		for level, expected in cases:
			with self.subTest(level=level):
				payload = _apns_prepare(
					"123", "interruption level just arrived", interruption_level=level
				).dict()
				self.assertEqual(payload["aps"]["interruption-level"], expected)

	def test_interruption_level_edge_cases(self):
		payload = _apns_prepare("123", "Happy django's day!").dict()
		self.assertNotIn("interruption-level", payload["aps"])

		for invalid in ("invalid", 42):
			with self.subTest(invalid=invalid):
				with self.assertRaises(ValueError):
					_apns_prepare("123", "sample", interruption_level=invalid)

		with mock.patch("push_notifications.apns._apns_send", return_value={}) as s:
			apns_send_message(
				"123", "Vibes and Customer Service Week 2026.",
				interruption_level=InterruptionLevelType.PASSIVE,
			)
			apns_send_bulk_message(
				["123", "456"], "Happy django's day!",
				interruption_level=InterruptionLevelType.CRITICAL,
			)
		self.assertEqual(
			s.call_args_list[0][1]["interruption_level"], "passive"
		)
		self.assertEqual(
			s.call_args_list[1][1]["interruption_level"], "critical"
		)
