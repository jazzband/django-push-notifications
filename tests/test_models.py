from __future__ import absolute_import
import json

from django.test import TestCase
from django.utils import timezone
from push_notifications.gcm import GCMError, send_bulk_message
from push_notifications.models import APNSDevice, GCMDevice
from . import responses
from ._mock import mock


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

	def test_gcm_send_message(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="GCM")
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"data": {"message": "Hello world"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_gcm_send_message_extra(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="GCM")
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world", extra={"foo": "bar"}, collapse_key="test_key")
			p.assert_called_once_with(
				json.dumps({
					"collapse_key": "test_key",
					"data": {"message": "Hello world", "foo": "bar"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_gcm_send_message_collapse_key(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="GCM")
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world", collapse_key="test_key")
			p.assert_called_once_with(
				json.dumps({
					"data": {"message": "Hello world"},
					"registration_ids": ["abc"],
					"collapse_key": "test_key"
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_gcm_send_message_to_multiple_devices(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"data": {"message": "Hello world"},
					"registration_ids": ["abc", "abc1"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_gcm_send_message_active_devices(self):
		GCMDevice.objects.create(registration_id="abc", active=True, cloud_message_type="GCM")
		GCMDevice.objects.create(registration_id="xyz", active=False, cloud_message_type="GCM")

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"data": {"message": "Hello world"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_gcm_send_message_collapse_to_multiple_devices(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_MULTIPLE
		) as p:
				GCMDevice.objects.all().send_message("Hello world", collapse_key="test_key")
				p.assert_called_once_with(
					json.dumps({
						"collapse_key": "test_key",
						"data": {"message": "Hello world"},
						"registration_ids": ["abc", "abc1"]
					}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
					"application/json", application_id=None
				)

	def test_gcm_send_message_to_single_device_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "abc1"]
		self._create_devices(devices)

		errors = [
			responses.GCM_JSON_ERROR_NOTREGISTERED,
			responses.GCM_JSON_ERROR_INVALIDREGISTRATION
		]
		for index, error in enumerate(errors):
			with mock.patch(
				"push_notifications.gcm._gcm_send", return_value=error):
				device = GCMDevice.objects.get(registration_id=devices[index])
				device.send_message("Hello World!")
				assert GCMDevice.objects.get(registration_id=devices[index]).active is False

	def test_gcm_send_message_to_single_device_with_error_mismatch(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="GCM")

		with mock.patch(
			"push_notifications.gcm._gcm_send",
			return_value=responses.GCM_JSON_ERROR_MISMATCHSENDERID
		):
			# these errors are not device specific, GCMError should be thrown
			with self.assertRaises(GCMError):
				device.send_message("Hello World!")
			assert GCMDevice.objects.get(registration_id="abc").active is True

	def test_gcm_send_message_to_multiple_devices_with_error(self):
		self._create_devices(["abc", "abc1", "abc2"])
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_MULTIPLE_ERROR
		):
			devices = GCMDevice.objects.all()
			devices.send_message("Hello World")
			assert not GCMDevice.objects.get(registration_id="abc").active
			assert GCMDevice.objects.get(registration_id="abc1").active
			assert not GCMDevice.objects.get(registration_id="abc2").active

	def test_gcm_send_message_to_multiple_devices_with_error_b(self):
		self._create_devices(["abc", "abc1", "abc2"])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_MULTIPLE_ERROR_B
		):
			devices = GCMDevice.objects.all()
			with self.assertRaises(GCMError):
				devices.send_message("Hello World")
			assert GCMDevice.objects.get(registration_id="abc").active is True
			assert GCMDevice.objects.get(registration_id="abc1").active is True
			assert GCMDevice.objects.get(registration_id="abc2").active is False

	def test_gcm_send_message_to_multiple_devices_with_canonical_id(self):
		self._create_devices(["foo", "bar"])
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_MULTIPLE_CANONICAL_ID
		):
			GCMDevice.objects.all().send_message("Hello World")
			assert not GCMDevice.objects.filter(registration_id="foo").exists()
			assert GCMDevice.objects.filter(registration_id="bar").exists()
			assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists() is True

	def test_gcm_send_message_to_single_user_with_canonical_id(self):
		old_registration_id = "foo"
		self._create_devices([old_registration_id])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=responses.GCM_JSON_CANONICAL_ID
		):
			GCMDevice.objects.get(registration_id=old_registration_id).send_message("Hello World")
			assert not GCMDevice.objects.filter(registration_id=old_registration_id).exists()
			assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists()

	def test_gcm_send_message_to_same_devices_with_canonical_id(self):
		first_device = GCMDevice.objects.create(
			registration_id="foo", active=True, cloud_message_type="GCM"
		)
		second_device = GCMDevice.objects.create(
			registration_id="bar", active=False, cloud_message_type="GCM"
		)

		with mock.patch(
			"push_notifications.gcm._gcm_send",
			return_value=responses.GCM_JSON_CANONICAL_ID_SAME_DEVICE
		):
			GCMDevice.objects.all().send_message("Hello World")

		assert first_device.active is True
		assert second_device.active is False

	def test_gcm_send_message_with_no_reg_ids(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch("push_notifications.gcm._cm_send_request", return_value="") as p:
			GCMDevice.objects.filter(registration_id="xyz").send_message("Hello World")
			p.assert_not_called()

		with mock.patch("push_notifications.gcm._cm_send_request", return_value="") as p:
			reg_ids = [obj.registration_id for obj in GCMDevice.objects.all()]
			send_bulk_message(reg_ids, {"message": "Hello World"}, "GCM")
			p.assert_called_once_with(
				[u"abc", u"abc1"], {"message": "Hello World"}, cloud_type="GCM", application_id=None
			)

	def test_fcm_send_message(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"notification": {"body": "Hello world"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_fcm_send_message_extra_data(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world", extra={"foo": "bar"})
			p.assert_called_once_with(
				json.dumps({
					"data": {"foo": "bar"},
					"notification": {"body": "Hello world"},
					"registration_ids": ["abc"],
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json",
				application_id=None
			)

	def test_fcm_send_message_extra_options(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world", collapse_key="test_key", foo="bar")
			p.assert_called_once_with(
				json.dumps({
					"collapse_key": "test_key",
					"notification": {"body": "Hello world"},
					"registration_ids": ["abc"],
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json",
				application_id=None
			)

	def test_fcm_send_message_extra_notification(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message("Hello world", extra={"icon": "test_icon"}, title="test")
			p.assert_called_once_with(
				json.dumps({
					"notification": {"body": "Hello world", "title": "test", "icon": "test_icon"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_fcm_send_message_extra_options_and_notification_and_data(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON
		) as p:
			device.send_message(
				"Hello world",
				extra={"foo": "bar", "icon": "test_icon"},
				title="test",
				collapse_key="test_key"
			)
			p.assert_called_once_with(
				json.dumps({
					"notification": {"body": "Hello world", "title": "test", "icon": "test_icon"},
					"data": {"foo": "bar"},
					"registration_ids": ["abc"],
					"collapse_key": "test_key"
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_fcm_send_message_to_multiple_devices(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"notification": {"body": "Hello world"},
					"registration_ids": ["abc", "abc1"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_fcm_send_message_active_devices(self):
		GCMDevice.objects.create(registration_id="abc", active=True, cloud_message_type="FCM")
		GCMDevice.objects.create(registration_id="xyz", active=False, cloud_message_type="FCM")

		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_MULTIPLE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"notification": {"body": "Hello world"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
				"application/json", application_id=None
			)

	def test_fcm_send_message_collapse_to_multiple_devices(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_MULTIPLE
		) as p:
				GCMDevice.objects.all().send_message("Hello world", collapse_key="test_key")
				p.assert_called_once_with(
					json.dumps({
						"collapse_key": "test_key",
						"notification": {"body": "Hello world"},
						"registration_ids": ["abc", "abc1"]
					}, separators=(",", ":"), sort_keys=True).encode("utf-8"),
					"application/json", application_id=None
				)

	def test_fcm_send_message_to_single_device_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "abc1"]
		self._create_fcm_devices(devices)

		errors = [
			responses.GCM_JSON_ERROR_NOTREGISTERED,
			responses.GCM_JSON_ERROR_INVALIDREGISTRATION
		]
		for index, error in enumerate(errors):
			with mock.patch(
				"push_notifications.gcm._fcm_send", return_value=error):
				device = GCMDevice.objects.get(registration_id=devices[index])
				device.send_message("Hello World!")
				assert GCMDevice.objects.get(registration_id=devices[index]).active is False

	def test_fcm_send_message_to_single_device_with_error_mismatch(self):
		device = GCMDevice.objects.create(registration_id="abc", cloud_message_type="FCM")

		with mock.patch(
			"push_notifications.gcm._fcm_send",
			return_value=responses.GCM_JSON_ERROR_MISMATCHSENDERID
		):
			# these errors are not device specific, GCMError should be thrown
			with self.assertRaises(GCMError):
				device.send_message("Hello World!")
			assert GCMDevice.objects.get(registration_id="abc").active is True

	def test_fcm_send_message_to_multiple_devices_with_error(self):
		self._create_fcm_devices(["abc", "abc1", "abc2"])
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_MULTIPLE_ERROR
		):
			devices = GCMDevice.objects.all()
			devices.send_message("Hello World")
			assert not GCMDevice.objects.get(registration_id="abc").active
			assert GCMDevice.objects.get(registration_id="abc1").active
			assert not GCMDevice.objects.get(registration_id="abc2").active

	def test_fcm_send_message_to_multiple_devices_with_error_b(self):
		self._create_fcm_devices(["abc", "abc1", "abc2"])

		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_MULTIPLE_ERROR_B
		):
			devices = GCMDevice.objects.all()
			with self.assertRaises(GCMError):
				devices.send_message("Hello World")
			assert GCMDevice.objects.get(registration_id="abc").active is True
			assert GCMDevice.objects.get(registration_id="abc1").active is True
			assert GCMDevice.objects.get(registration_id="abc2").active is False

	def test_fcm_send_message_to_multiple_devices_with_canonical_id(self):
		self._create_fcm_devices(["foo", "bar"])
		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_MULTIPLE_CANONICAL_ID
		):
			GCMDevice.objects.all().send_message("Hello World")
			assert not GCMDevice.objects.filter(registration_id="foo").exists()
			assert GCMDevice.objects.filter(registration_id="bar").exists()
			assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists() is True

	def test_fcm_send_message_to_single_user_with_canonical_id(self):
		old_registration_id = "foo"
		self._create_fcm_devices([old_registration_id])

		with mock.patch(
			"push_notifications.gcm._fcm_send", return_value=responses.GCM_JSON_CANONICAL_ID
		):
			GCMDevice.objects.get(registration_id=old_registration_id).send_message("Hello World")
			assert not GCMDevice.objects.filter(registration_id=old_registration_id).exists()
			assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists()

	def test_fcm_send_message_to_same_devices_with_canonical_id(self):
		first_device = GCMDevice.objects.create(
			registration_id="foo", active=True, cloud_message_type="FCM"
		)
		second_device = GCMDevice.objects.create(
			registration_id="bar", active=False, cloud_message_type="FCM"
		)

		with mock.patch(
			"push_notifications.gcm._fcm_send",
			return_value=responses.GCM_JSON_CANONICAL_ID_SAME_DEVICE
		):
			GCMDevice.objects.all().send_message("Hello World")

		assert first_device.active is True
		assert second_device.active is False

	def test_fcm_send_message_with_no_reg_ids(self):
		self._create_fcm_devices(["abc", "abc1"])

		with mock.patch("push_notifications.gcm._cm_send_request", return_value="") as p:
			GCMDevice.objects.filter(registration_id="xyz").send_message("Hello World")
			p.assert_not_called()

		with mock.patch("push_notifications.gcm._cm_send_request", return_value="") as p:
			reg_ids = [obj.registration_id for obj in GCMDevice.objects.all()]
			send_bulk_message(reg_ids, {"message": "Hello World"}, "FCM")
			p.assert_called_once_with(
				[u"abc", u"abc1"], {"message": "Hello World"}, cloud_type="FCM",
				application_id=None
			)

	def test_can_save_wsn_device(self):
		device = GCMDevice.objects.create(registration_id="a valid registration id")
		self.assertIsNotNone(device.pk)
		self.assertIsNotNone(device.date_created)
		self.assertEqual(device.date_created.date(), timezone.now().date())
