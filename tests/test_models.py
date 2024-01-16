from unittest import mock

from django.test import TestCase
from django.utils import timezone
from firebase_admin import messaging
from firebase_admin.exceptions import InvalidArgumentError
from firebase_admin.messaging import BatchResponse, Message, SendResponse

from push_notifications.gcm import dict_to_fcm_message, send_bulk_message
from push_notifications.models import APNSDevice, GCMDevice

from . import responses


class GCMModelTestCase(TestCase):
	def _create_devices(self, devices):
		for device in devices:
			GCMDevice.objects.create(registration_id=device, cloud_message_type="GCM")

	def _create_fcm_devices(self, devices):
		for device in devices:
			GCMDevice.objects.create(registration_id=device, cloud_message_type="FCM")

	def test_can_save_gcm_device(self):
		device = GCMDevice.objects.create(
			registration_id="a valid registration id", cloud_message_type="GCM"
		)
		assert device.id is not None
		assert device.date_created is not None
		assert device.date_created.date() == timezone.now().date()

	def test_can_create_save_device(self):
		device = APNSDevice.objects.create(registration_id="a valid registration id")
		assert device.id is not None
		assert device.date_created is not None
		assert device.date_created.date() == timezone.now().date()

	def test_fcm_send_message(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world")

			# one call
			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# only one message
			self.assertEqual(len(call.args[0]), 1)

			message = call.args[0][0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")

	def test_fcm_send_message_extra_data(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world", extra={"foo": "bar"})

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# only one message
			self.assertEqual(len(call.args[0]), 1)

			message = call.args[0][0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.data, {"foo": "bar"})

	def test_fcm_send_message_extra_options(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world", collapse_key="test_key", foo="bar")

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# only one message
			self.assertEqual(len(call.args[0]), 1)

			message = call.args[0][0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.android.collapse_key, "test_key")
			self.assertFalse(message.data)

	def test_fcm_send_message_extra_notification(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world", extra={"icon": "test_icon"}, title="test")

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# only one message
			self.assertEqual(len(call.args[0]), 1)

			message = call.args[0][0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.android.notification.title, "test")
			self.assertEqual(message.android.notification.icon, "test_icon")
			self.assertFalse(message.data)

	def test_fcm_send_message_extra_options_and_notification_and_data(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message(
				"Hello world",
				extra={"foo": "bar", "icon": "test_icon"},
				title="test",
				collapse_key="test_key"
			)

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# only one message
			self.assertEqual(len(call.args[0]), 1)

			message = call.args[0][0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.collapse_key, "test_key")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.android.notification.title, "test")
			self.assertEqual(message.android.notification.icon, "test_icon")
			self.assertEqual(message.data, {"foo": "bar"})

	def test_fcm_send_message_to_multiple_devices(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# two messages
			self.assertEqual(len(call.args[0]), 2)

			message_one = call.args[0][0]
			message_two = call.args[0][1]
			self.assertIsInstance(message_one, Message)
			self.assertIsInstance(message_two, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_two.token, "abc1")
			self.assertEqual(message_one.android.notification.body, "Hello world")
			self.assertEqual(message_two.android.notification.body, "Hello world")

	def test_fcm_send_message_active_devices(self):
		GCMDevice.objects.create(registration_id="abc", active=True, cloud_message_type="FCM")
		GCMDevice.objects.create(registration_id="xyz", active=False, cloud_message_type="FCM")

		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# only one message (one is inactive)
			self.assertEqual(len(call.args[0]), 1)
			message_one = call.args[0][0]

			self.assertIsInstance(message_one, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_one.android.notification.body, "Hello world")

	def test_fcm_send_message_collapse_to_multiple_devices(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world", collapse_key="test_key")

			self.assertEqual(len(p.mock_calls), 1)
			call = p.mock_calls[0]

			# only messages is args, dry_run and app are in kwargs
			self.assertEqual(len(call.args), 1)

			self.assertTrue("dry_run" in call.kwargs)
			self.assertFalse(call.kwargs["dry_run"])
			self.assertTrue("app" in call.kwargs)
			self.assertIsNone(call.kwargs["app"])

			# two messages
			self.assertEqual(len(call.args[0]), 2)

			message_one = call.args[0][0]
			message_two = call.args[0][1]
			self.assertIsInstance(message_one, Message)
			self.assertIsInstance(message_two, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_two.token, "abc1")
			self.assertEqual(message_one.android.collapse_key, "test_key")
			self.assertEqual(message_two.android.collapse_key, "test_key")

	def test_fcm_send_message_to_single_device_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "abc1", "abc2"]
		self._create_fcm_devices(devices)

		errors = [
			messaging.UnregisteredError("error"),
			messaging.SenderIdMismatchError("error"),
			InvalidArgumentError("Invalid registration"),
		]

		for index, error in enumerate(errors):
			return_value = BatchResponse(
				[SendResponse(resp={"name": "..."}, exception=error)]
			)
			with mock.patch(
				"firebase_admin.messaging.send_all", return_value=return_value
			):
				device = GCMDevice.objects.get(registration_id=devices[index])
				device.send_message("Hello World!")
				self.assertFalse(GCMDevice.objects.get(registration_id=devices[index]).active)

	def test_fcm_send_message_to_single_device_with_error_mismatch(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")

		return_value = BatchResponse(
			[SendResponse(resp={"name": "..."}, exception=OSError())]
		)
		with mock.patch(
			"firebase_admin.messaging.send_all",
			return_value=return_value
		):
			# these errors are not device specific, device is not deactivated
			response = device.send_message("Hello World!")
			self.assertTrue(GCMDevice.objects.get(registration_id="abc").active)
			self.assertEqual(response.failure_count, 1)

	def test_fcm_send_message_to_multiple_devices_with_error(self):
		self._create_fcm_devices(["abc", "abc1", "abc2", "abc3"])

		return_value = BatchResponse([
			SendResponse(resp={"name": "..."}, exception=messaging.UnregisteredError("error")),
			SendResponse(resp={"name": "..."}, exception=messaging.SenderIdMismatchError("error")),
			SendResponse(resp={"name": "..."}, exception=OSError()),
			SendResponse(resp={"name": "..."}, exception=InvalidArgumentError("Invalid registration")),
		])
		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=return_value
		):
			GCMDevice.objects.all().send_message("Hello World")
			self.assertFalse(GCMDevice.objects.get(registration_id="abc").active)
			self.assertFalse(GCMDevice.objects.get(registration_id="abc1").active)
			self.assertTrue(GCMDevice.objects.get(registration_id="abc2").active)
			self.assertFalse(GCMDevice.objects.get(registration_id="abc3").active)

	def test_fcm_send_message_to_multiple_devices_with_error_b(self):
		self._create_fcm_devices(["abc", "abc1", "abc2", "abc3"])

		return_value = BatchResponse([
			SendResponse(resp={"name": "..."}, exception=OSError()),
			SendResponse(resp={"name": "..."}, exception=OSError()),
			SendResponse(resp={"name": "..."}, exception=messaging.UnregisteredError("error")),
			SendResponse(resp={"name": "..."}, exception=OSError()),
		])

		with mock.patch(
			"firebase_admin.messaging.send_all", return_value=return_value
		):
			GCMDevice.objects.all().send_message("Hello World")
			self.assertTrue(GCMDevice.objects.get(registration_id="abc").active)
			self.assertTrue(GCMDevice.objects.get(registration_id="abc1").active)
			self.assertFalse(GCMDevice.objects.get(registration_id="abc2").active)
			self.assertTrue(GCMDevice.objects.get(registration_id="abc3").active)

	def test_fcm_send_message_with_no_reg_ids(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_all",
			return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.filter(registration_id="xyz").send_message("Hello World")
			p.assert_not_called()

		with mock.patch(
			"firebase_admin.messaging.send_all",
			return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			reg_ids = [obj.registration_id for obj in GCMDevice.objects.all()]
			message = dict_to_fcm_message({"message": "Hello World"})
			send_bulk_message(reg_ids, message)
			p.assert_called_once()

	def test_can_save_wsn_device(self):
		device = GCMDevice.objects.create(registration_id="a valid registration id")
		self.assertIsNotNone(device.pk)
		self.assertIsNotNone(device.date_created)
		self.assertEqual(device.date_created.date(), timezone.now().date())
