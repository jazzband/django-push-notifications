import sys
import time
from unittest import mock

import pytest
from django.test import TestCase

try:

	from push_notifications.apns_async import (
		TokenCredentials,
		apns_send_message,
	)
except ModuleNotFoundError:
	# skipping because apns2 is not supported on python 3.10
	# it uses hyper that imports from collections which were changed in 3.10
	# and we would get  "AttributeError: module 'collections' has no attribute 'MutableMapping'"
	if sys.version_info < (3, 10):
		pytest.skip(allow_module_level=True)
	else:
		raise



class APNSAsyncPushPayloadTest(TestCase):
	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload(self, mock_apns):
		_res = apns_send_message(
			"123",
			"Hello world",
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
			badge=1,
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)
		self.assertTrue(mock_apns.called)
		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]
		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "Hello world")
		self.assertEqual(req.message["aps"]["badge"], 1)
		self.assertEqual(req.message["aps"]["sound"], "chime")
		self.assertEqual(req.message["custom_data"], 12345)
		self.assertEqual(req.time_to_live, 3)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_thread_id(self, mock_apns):
		_res = apns_send_message(
			"123",
			"Hello world",
			thread_id="565",
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)
		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "Hello world")
		self.assertEqual(req.message["aps"]["thread-id"], "565")
		self.assertEqual(req.message["aps"]["sound"], "chime")
		self.assertEqual(req.message["custom_data"], 12345)
		self.assertAlmostEqual(req.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_alert_dict(self, mock_apns):
		_res = apns_send_message(
			"123",
			alert={"title": "t1", "body": "b1"},
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"]["body"], "b1")
		self.assertEqual(req.message["aps"]["alert"]["title"], "t1")
		self.assertEqual(req.message["aps"]["sound"], "chime")
		self.assertEqual(req.message["custom_data"], 12345)
		self.assertAlmostEqual(req.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_localised_push_with_empty_body(self, mock_apns):
		_res = apns_send_message(
			"123",
			None,
			loc_key="TEST_LOC_KEY",
			expiration=time.time() + 3,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, _kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"]["loc-key"], "TEST_LOC_KEY")
		self.assertAlmostEqual(req.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_using_extra(self, mock_apns):
		apns_send_message(
			"123",
			"sample",
			extra={"foo": "bar"},
			expiration=(time.time() + 30),
			priority=10,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, _kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "sample")
		self.assertEqual(req.message["foo"], "bar")
		self.assertEqual(req.priority, 10)
		self.assertAlmostEqual(req.time_to_live, 30, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_collapse_id(self, mock_apns):
		_res = apns_send_message(
			"123",
			"sample",
			collapse_id="456789",
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "sample")
		self.assertEqual(req.collapse_key, "456789")

	# def test_bad_priority(self):
	# 	with mock.patch("apns2.credentials.init_context"):
	# 		with mock.patch("apns2.client.APNsClient.connect"):
	# 			with mock.patch("apns2.client.APNsClient.send_notification") as s:
	# 				self.assertRaises(APNSUnsupportedPriority, _apns_send, "123", "_" * 2049, priority=24)
	# 			s.assert_has_calls([])
