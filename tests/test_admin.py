from unittest import mock

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.test import TestCase
from firebase_admin.messaging import BatchResponse, Message, SendResponse, UnregisteredError

from push_notifications.admin import DeviceAdmin, GCMDeviceAdmin, WebPushDeviceAdmin
from push_notifications.models import APNSDevice, GCMDevice, WebPushDevice, WNSDevice
from push_notifications.wns import WNSNotificationResponseError
from tests import responses


class WebPushDeviceAdminTestCase(TestCase):
	def test_bulk_action_with_only_inactive_devices_does_not_crash_or_claim_success(self):
		WebPushDevice.objects.create(registration_id="inactive", active=False)
		admin = WebPushDeviceAdmin(WebPushDevice, AdminSite())
		admin.message_user = mock.Mock()

		admin.send_messages(HttpRequest(), WebPushDevice.objects.all(), bulk=True)

		admin.message_user.assert_not_called()

	def test_bulk_action_reports_first_failed_webpush_with_later_success(self):
		WebPushDevice.objects.create(registration_id="failed", active=True)
		WebPushDevice.objects.create(registration_id="ok", active=True)
		admin = WebPushDeviceAdmin(WebPushDevice, AdminSite())
		admin.message_user = mock.Mock()

		def send(device, message):
			if device.registration_id == "failed":
				return {"failure": 1, "results": [{"error": "expired"}]}
			return {"success": 1, "results": [{}]}

		with mock.patch("push_notifications.webpush.webpush_send_message", side_effect=send):
			admin.send_messages(HttpRequest(), WebPushDevice.objects.order_by("id"), bulk=True)

		self.assertEqual(admin.message_user.call_args_list[0].kwargs["level"], messages.ERROR)
		self.assertIn("expired", str(admin.message_user.call_args_list[0].args[1]))


class WNSDeviceAdminTestCase(TestCase):
	def test_bulk_action_reports_string_responses_without_crashing(self):
		WNSDevice.objects.create(registration_id="urn:device", application_id="app")
		admin = DeviceAdmin(WNSDevice, AdminSite())
		admin.message_user = mock.Mock()

		with mock.patch("push_notifications.wns.wns_send_bulk_message", return_value=["ok"]):
			admin.send_messages(HttpRequest(), WNSDevice.objects.all(), bulk=True)

		admin.message_user.assert_called_once()
		self.assertNotEqual(admin.message_user.call_args.kwargs.get("level"), messages.ERROR)

	def test_bulk_action_reports_wns_failure(self):
		WNSDevice.objects.create(registration_id="urn:expired", application_id="app")
		admin = DeviceAdmin(WNSDevice, AdminSite())
		admin.message_user = mock.Mock()

		with mock.patch(
			"push_notifications.wns.wns_send_bulk_message",
			side_effect=WNSNotificationResponseError("HTTP 410"),
		):
			admin.send_messages(HttpRequest(), WNSDevice.objects.all(), bulk=True)

		admin.message_user.assert_called_once()
		self.assertEqual(admin.message_user.call_args.kwargs["level"], messages.ERROR)
		self.assertIn("HTTP 410", str(admin.message_user.call_args.args[1]))


class APNSDeviceAdminTestCase(TestCase):
	def test_bulk_action_reports_failures_from_later_application_group(self):
		APNSDevice.objects.create(registration_id="first", application_id="a")
		APNSDevice.objects.create(registration_id="second", application_id="b")
		admin = DeviceAdmin(APNSDevice, AdminSite())
		admin.message_user = mock.Mock()

		def send_group(registration_ids, **kwargs):
			status = "Success" if registration_ids[0] == "first" else "Unregistered"
			return {registration_ids[0]: status}

		with mock.patch(
			"push_notifications.apns_async.apns_send_bulk_message", side_effect=send_group
		):
			admin.send_messages(HttpRequest(), APNSDevice.objects.all(), bulk=True)

		self.assertIn("Unregistered", str(admin.message_user.call_args_list[0].args[1]))
		self.assertEqual(admin.message_user.call_args_list[0].kwargs["level"], messages.ERROR)


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
