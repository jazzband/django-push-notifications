import sys
from unittest import mock

import pytest


try:
	from apns2.client import NotificationPriority
	from apns2.errors import BadTopic, PayloadTooLarge, Unregistered
	from django.conf import settings
	from django.test import TestCase, override_settings

	from push_notifications.exceptions import APNSError
	from push_notifications.models import APNSDevice
except (AttributeError, ModuleNotFoundError):
	# skipping because apns2 is not supported on python 3.10
	# it uses hyper that imports from collections which were changed in 3.10
	# and we would get  "AttributeError: module 'collections' has no attribute 'MutableMapping'"
	if sys.version_info >= (3, 10):
		pytest.skip(allow_module_level=True)
	else:
		raise

class APNSModelTestCase(TestCase):
	def _create_devices(self, devices):
		for device in devices:
			APNSDevice.objects.create(registration_id=device)

	@override_settings()
	def test_apns_send_bulk_message(self):
		self._create_devices(["abc", "def"])

		# legacy conf manager requires a value
		settings.PUSH_NOTIFICATIONS_SETTINGS.update(
			{"APNS_CERTIFICATE": "/path/to/apns/certificate.pem"}
		)

		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification_batch") as s:
					APNSDevice.objects.all().send_message("Hello world", expiration=1)
					args, kargs = s.call_args
					self.assertEqual(args[0][0].token, "abc")
					self.assertEqual(args[0][1].token, "def")
					self.assertEqual(args[0][0].payload.alert, "Hello world")
					self.assertEqual(args[0][1].payload.alert, "Hello world")
					self.assertEqual(kargs["expiration"], 1)

	def test_apns_send_message_extra(self):
		self._create_devices(["abc"])

		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					APNSDevice.objects.get().send_message(
						"Hello world", expiration=2, priority=5, extra={"foo": "bar"}
					)
					args, kargs = s.call_args
					self.assertEqual(args[0], "abc")
					self.assertEqual(args[1].alert, "Hello world")
					self.assertEqual(args[1].custom, {"foo": "bar"})
					self.assertEqual(kargs["priority"], NotificationPriority.Delayed)
					self.assertEqual(kargs["expiration"], 2)

	def test_apns_send_message(self):
		self._create_devices(["abc"])

		with mock.patch("apns2.credentials.init_context"):
			with mock.patch("apns2.client.APNsClient.connect"):
				with mock.patch("apns2.client.APNsClient.send_notification") as s:
					APNSDevice.objects.get().send_message("Hello world", expiration=1)
					args, kargs = s.call_args
					self.assertEqual(args[0], "abc")
					self.assertEqual(args[1].alert, "Hello world")
					self.assertEqual(kargs["expiration"], 1)

	def test_apns_send_message_to_single_device_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc"]
		self._create_devices(devices)

		with mock.patch("push_notifications.apns._apns_send") as s:
			s.side_effect = Unregistered
			device = APNSDevice.objects.get(registration_id="abc")
			with self.assertRaises(APNSError) as ae:
				device.send_message("Hello World!")
			self.assertEqual(ae.exception.status, "Unregistered")
			self.assertFalse(APNSDevice.objects.get(registration_id="abc").active)

	def test_apns_send_message_to_several_devices_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "def", "ghi"]
		expected_exceptions_statuses = ["PayloadTooLarge", "BadTopic", "Unregistered"]
		self._create_devices(devices)

		with mock.patch("push_notifications.apns._apns_send") as s:
			s.side_effect = [PayloadTooLarge, BadTopic, Unregistered]

			for idx, token in enumerate(devices):
				device = APNSDevice.objects.get(registration_id=token)
				with self.assertRaises(APNSError) as ae:
					device.send_message("Hello World!")
				self.assertEqual(ae.exception.status, expected_exceptions_statuses[idx])

				if idx == 2:
					self.assertFalse(
						APNSDevice.objects.get(registration_id=token).active
					)
				else:
					self.assertTrue(
						APNSDevice.objects.get(registration_id=token).active
					)

	def test_apns_send_message_to_bulk_devices_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "def", "ghi"]
		results = {"abc": "PayloadTooLarge", "def": "BadTopic", "ghi": "Unregistered"}
		self._create_devices(devices)

		with mock.patch("push_notifications.apns._apns_send") as s:
			s.return_value = results

			results = APNSDevice.objects.all().send_message("Hello World!")

			for idx, token in enumerate(devices):
				if idx == 2:
					self.assertFalse(
						APNSDevice.objects.get(registration_id=token).active
					)
				else:
					self.assertTrue(
						APNSDevice.objects.get(registration_id=token).active
					)

	def test_apns_send_message_to_duplicated_device_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "abc"]
		self._create_devices(devices)

		with mock.patch("push_notifications.apns._apns_send") as s:
			s.side_effect = Unregistered
			device = APNSDevice.objects.filter(registration_id="abc").first()
			with self.assertRaises(APNSError) as ae:
				device.send_message("Hello World!")
			self.assertEqual(ae.exception.status, "Unregistered")
			for device in APNSDevice.objects.filter(registration_id="abc"):
				self.assertFalse(device.active)
