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
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world")

			# one call
			self.assertEqual(len(p.mock_calls), 1)

			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")

	def test_fcm_send_message_with_fcm_message(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			message_to_send = messaging.Message(
				notification=messaging.Notification(
					title='Hello world',
					body='What a beautiful day.'
				),
			)
			device.send_message(message_to_send)

			# one call
			self.assertEqual(len(p.mock_calls), 1)

			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.notification.body, "What a beautiful day.")
			self.assertEqual(message.notification.title, "Hello world")

	def test_fcm_send_message_extra_data(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world", extra={"foo": "bar"})

			self.assertEqual(len(p.mock_calls), 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.data, {"foo": "bar"})

	def test_fcm_send_message_extra_options(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world", collapse_key="test_key", foo="bar")

			self.assertEqual(len(p.mock_calls), 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.android.collapse_key, "test_key")
			self.assertFalse(message.data)

	def test_fcm_send_message_extra_notification(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message("Hello world", extra={"icon": "test_icon"}, title="test")

			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")
			self.assertEqual(message.android.notification.title, "test")
			self.assertEqual(message.android.notification.icon, "test_icon")
			self.assertFalse(message.data)

	def test_fcm_send_message_extra_options_and_notification_and_data(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			device.send_message(
				"Hello world",
				extra={"foo": "bar", "icon": "test_icon"},
				title="test",
				collapse_key="test_key"
			)

			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
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
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")

			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# two messages
			messages = call[0][0]
			self.assertEqual(len(messages), 2)

			message_one = messages[0]
			message_two = messages[1]
			self.assertIsInstance(message_one, Message)
			self.assertIsInstance(message_two, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_two.token, "abc1")
			self.assertEqual(message_one.android.notification.body, "Hello world")
			self.assertEqual(message_two.android.notification.body, "Hello world")

	def test_fcm_send_message_to_multiple_devices_fcm_message(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			message_to_send = messaging.Message(
				notification=messaging.Notification(
					title='Hello world',
					body='What a beautiful day.'
				),
			)
			GCMDevice.objects.all().send_message(message_to_send)

			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# two messages
			messages = call[0][0]
			self.assertEqual(len(messages), 2)

			message_one = messages[0]
			message_two = messages[1]
			self.assertIsInstance(message_one, Message)
			self.assertIsInstance(message_two, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_two.token, "abc1")
			self.assertEqual(message_one.notification.title, "Hello world")
			self.assertEqual(message_one.notification.body, "What a beautiful day.")
			self.assertEqual(message_two.notification.title, "Hello world")
			self.assertEqual(message_two.notification.body, "What a beautiful day.")

	def test_gcm_send_message_does_not_send(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="GCM")

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			message_to_send = messaging.Message(
				notification=messaging.Notification(
					title='Hello world',
					body='What a beautiful day.'
				),
			)
			response = device.send_message(message_to_send)
			self.assertIsNone(response)
			self.assertEqual(p.call_count, 0)

	def test_gcm_send_multiple_message_does_not_send(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			message_to_send = messaging.Message(
				notification=messaging.Notification(
					title='Hello world',
					body='What a beautiful day.'
				),
			)
			response = GCMDevice.objects.all().send_message(message_to_send).responses

			self.assertEqual(p.call_count, 0)
			self.assertEqual(len(response), 0)


	def test_fcm_send_message_active_devices(self):
		GCMDevice.objects.create(registration_id="abc", active=True, cloud_message_type="FCM")
		GCMDevice.objects.create(registration_id="xyz", active=False, cloud_message_type="FCM")

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")

			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message (one is inactive)
			messages = call[0][0]
			self.assertEqual(len(messages), 1)
			message_one = messages[0]

			self.assertIsInstance(message_one, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_one.android.notification.body, "Hello world")

	def test_fcm_send_message_collapse_to_multiple_devices(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world", collapse_key="test_key")

			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# two messages
			messages = call[0][0]
			self.assertEqual(len(messages), 2)

			message_one = messages[0]
			message_two = messages[1]
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
				"firebase_admin.messaging.send_each", return_value=return_value
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
			"firebase_admin.messaging.send_each",
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
			"firebase_admin.messaging.send_each", return_value=return_value
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
			"firebase_admin.messaging.send_each", return_value=return_value
		):
			GCMDevice.objects.all().send_message("Hello World")
			self.assertTrue(GCMDevice.objects.get(registration_id="abc").active)
			self.assertTrue(GCMDevice.objects.get(registration_id="abc1").active)
			self.assertFalse(GCMDevice.objects.get(registration_id="abc2").active)
			self.assertTrue(GCMDevice.objects.get(registration_id="abc3").active)

	def test_fcm_send_message_with_no_reg_ids(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"firebase_admin.messaging.send_each",
			return_value=responses.FCM_SUCCESS_MULTIPLE
		) as p:
			GCMDevice.objects.filter(registration_id="xyz").send_message("Hello World")
			p.assert_not_called()

		with mock.patch(
			"firebase_admin.messaging.send_each",
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
