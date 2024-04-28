import sys
from unittest import mock


from django.contrib.admin import AdminSite
from django.contrib import messages
from django.http import HttpRequest
from django.test import TestCase

from firebase_admin.messaging import Message, BatchResponse, SendResponse, UnregisteredError

from push_notifications.admin import GCMDeviceAdmin
from push_notifications.models import GCMDevice
from tests import responses


class GCMDeviceAdminTestCase(TestCase):
	def test_send_bulk_messages_action(self):
		request = HttpRequest()

		GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		queryset = GCMDevice.objects.all()
		admin = GCMDeviceAdmin(GCMDevice, AdminSite())
		admin.message_user = mock.Mock()

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			admin.send_messages(request, queryset, bulk=True)

			# one call
			self.assertEqual(len(p.mock_calls), 1)

			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			call_messages = call[0][0]
			self.assertEqual(len(call_messages), 1)

			message = call_messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Test bulk notification")

			admin.message_user.assert_called_once_with(
				request, "All messages were sent.", level=messages.SUCCESS
			)

	def test_send_single_message_action(self):
		request = HttpRequest()

		GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		queryset = GCMDevice.objects.all()
		admin = GCMDeviceAdmin(GCMDevice, AdminSite())
		admin.message_user = mock.Mock()

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=responses.FCM_SUCCESS
		) as p:
			admin.send_messages(request, queryset, bulk=False)

			# one call
			self.assertEqual(len(p.mock_calls), 1)

			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			call_messages = call[0][0]
			self.assertEqual(len(call_messages), 1)

			message = call_messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Test single notification")

			admin.message_user.assert_called_once_with(
				request, "All messages were sent.", level=messages.SUCCESS
			)

	def test_send_bulk_messages_action_fail(self):
		request = HttpRequest()

		GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		queryset = GCMDevice.objects.all()
		admin = GCMDeviceAdmin(GCMDevice, AdminSite())
		admin.message_user = mock.Mock()

		response = BatchResponse(
			[SendResponse(resp={"name": "..."}, exception=UnregisteredError("error"),)]
		)

		with mock.patch(
			"firebase_admin.messaging.send_each", return_value=response
		) as p:
			admin.send_messages(request, queryset, bulk=True)

			# one call
			self.assertEqual(len(p.mock_calls), 1)

			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			call_messages = call[0][0]
			self.assertEqual(len(call_messages), 1)

			message = call_messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Test bulk notification")

			error_message = "Some messages could not be processed: UnregisteredError('error')"

			admin.message_user.assert_called_once_with(
				request, error_message, level=messages.ERROR
			)
