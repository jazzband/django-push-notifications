import sys
import time
from unittest import mock

import pytest
from django.conf import settings
from django.test import TestCase, override_settings


try:
	from aioapns.common import NotificationResult

	from push_notifications.exceptions import APNSError
	from push_notifications.models import APNSDevice
except ModuleNotFoundError:
	# skipping because apns2 is not supported on python 3.10
	# it uses hyper that imports from collections which were changed in 3.10
	# and we would get  "AttributeError: module 'collections' has no attribute 'MutableMapping'"
	if sys.version_info < (3, 10):
		pytest.skip(allow_module_level=True)
	else:
		raise


class APNSModelTestCase(TestCase):
	def _create_devices(self, devices):
		for device in devices:
			APNSDevice.objects.create(registration_id=device)

	@override_settings()
	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_bulk_message(self, mock_apns):
		self._create_devices(["abc", "def"])

		# legacy conf manager requires a value
		settings.PUSH_NOTIFICATIONS_SETTINGS.update(
			{"APNS_CERTIFICATE": "/path/to/apns/certificate.pem"}
		)

		APNSDevice.objects.all().send_message("Hello world", expiration=time.time() + 3)

		[call1, call2] = mock_apns.return_value.send_notification.call_args_list
		req1 = call1.args[0]
		req2 = call2.args[0]

		self.assertEqual(req1.device_token, "abc")
		self.assertEqual(req2.device_token, "def")
		self.assertEqual(req1.message["aps"]["alert"], "Hello world")
		self.assertEqual(req2.message["aps"]["alert"], "Hello world")
		self.assertAlmostEqual(req1.time_to_live, 3, places=-1)
		self.assertAlmostEqual(req2.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_message_extra(self, mock_apns):
		self._create_devices(["abc"])
		APNSDevice.objects.get().send_message(
			"Hello world", expiration=time.time() + 2, priority=5, extra={"foo": "bar"}
		)

		args, kargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "abc")
		self.assertEqual(req.message["aps"]["alert"], "Hello world")
		self.assertEqual(req.message["foo"], "bar")
		self.assertEqual(req.priority, 5)
		self.assertAlmostEqual(req.time_to_live, 2, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_message(self, mock_apns):
		self._create_devices(["abc"])
		APNSDevice.objects.get().send_message("Hello world", expiration=time.time() + 1)

		args, kargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "abc")
		self.assertEqual(req.message["aps"]["alert"], "Hello world")
		self.assertAlmostEqual(req.time_to_live, 1, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_message_to_single_device_with_error(self, mock_apns):
		# these errors are device specific, device.active will be set false
		devices = ["abc"]
		self._create_devices(devices)

		mock_apns.return_value.send_notification.return_value = NotificationResult(
			status="400",
			notification_id="abc",
			description="PayloadTooLarge",
		)
		device = APNSDevice.objects.get(registration_id="abc")
		with self.assertRaises(APNSError) as ae:
			device.send_message("Hello World!")
		self.assertTrue("PayloadTooLarge" in ae.exception.message)
		self.assertTrue(APNSDevice.objects.get(registration_id="abc").active)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_message_to_several_devices_with_error(self, mock_apns):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "def", "ghi"]
		expected_exceptions_statuses = ["PayloadTooLarge", "DeviceTokenNotForTopic", "Unregistered"]
		self._create_devices(devices)

		mock_apns.return_value.send_notification.side_effect = [
			NotificationResult(
				status="400",
				notification_id="abc",
				description="PayloadTooLarge",
			),
			NotificationResult(
				status="400",
				notification_id="def",
				description="DeviceTokenNotForTopic",
			),
			NotificationResult(
				status="400",
				notification_id="ghi",
				description="Unregistered",
			),
		]

		for idx, token in enumerate(devices):
			device = APNSDevice.objects.get(registration_id=token)
			with self.assertRaises(APNSError) as ae:
				device.send_message("Hello World!")
			self.assertTrue(expected_exceptions_statuses[idx] in ae.exception.message)

			if idx == 0:
				self.assertTrue(APNSDevice.objects.get(registration_id=token).active)
			else:
				self.assertFalse(APNSDevice.objects.get(registration_id=token).active)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_message_to_bulk_devices_with_error(self, mock_apns):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "def", "ghi"]
		results = [
			NotificationResult(
				status="400",
				notification_id="abc",
				description="PayloadTooLarge",
			),
			NotificationResult(
				status="400",
				notification_id="def",
				description="DeviceTokenNotForTopic",
			),
			NotificationResult(
				status="400",
				notification_id="ghi",
				description="Unregistered",
			),
		]
		self._create_devices(devices)

		mock_apns.return_value.send_notification.side_effect = results

		with self.assertRaises(APNSError):
			APNSDevice.objects.all().send_message("Hello World!")

		for idx, token in enumerate(devices):
			if idx == 0:
				self.assertTrue(APNSDevice.objects.get(registration_id=token).active)
			else:
				self.assertFalse(APNSDevice.objects.get(registration_id=token).active)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_apns_send_messages_different_priority(self, mock_apns):
		self._create_devices(["abc", "def"])
		device_1 = APNSDevice.objects.get(registration_id="abc")
		device_2 = APNSDevice.objects.get(registration_id="def")

		device_1.send_message(
			"Hello world 1",
			expiration=time.time() + 1,
			priority=5,
			collapse_id="1",
		)
		args_1, _ = mock_apns.return_value.send_notification.call_args

		device_2.send_message("Hello world 2")
		args_2, _ = mock_apns.return_value.send_notification.call_args

		req = args_1[0]
		self.assertEqual(req.device_token, "abc")
		self.assertEqual(req.message["aps"]["alert"], "Hello world 1")
		self.assertAlmostEqual(req.time_to_live, 1, places=-1)
		self.assertEqual(req.priority, 5)
		self.assertEqual(req.collapse_key, "1")

		reg_2 = args_2[0]
		self.assertEqual(reg_2.device_token, "def")
		self.assertEqual(reg_2.message["aps"]["alert"], "Hello world 2")
		self.assertIsNone(reg_2.time_to_live, "No time to live should be specified")
		self.assertIsNone(reg_2.priority, "No priority should be specified")
		self.assertIsNone(reg_2.collapse_key, "No collapse key should be specified")
