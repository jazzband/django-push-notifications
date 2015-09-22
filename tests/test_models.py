import json
import mock
from django.test import TestCase
from django.utils import timezone
from push_notifications.models import GCMDevice, APNSDevice
from tests.mock_responses import GCM_PLAIN_RESPONSE, \
    GCM_MULTIPLE_JSON_RESPONSE, GCM_PLAIN_RESPONSE_ERROR, \
    GCM_JSON_RESPONSE_ERROR, GCM_PLAIN_RESPONSE_ERROR_B
from push_notifications.gcm import GCMError

class ModelTestCase(TestCase):
    def test_can_save_gcm_device(self):
        device = GCMDevice.objects.create(
            registration_id="a valid registration id"
        )
        assert device.id is not None
        assert device.date_created is not None
        assert device.date_created.date() == timezone.now().date()

    def test_can_create_save_device(self):
        device = APNSDevice.objects.create(
            registration_id="a valid registration id"
        )
        assert device.id is not None
        assert device.date_created is not None
        assert device.date_created.date() == timezone.now().date()

    def test_gcm_send_message(self):
        device = GCMDevice.objects.create(
            registration_id="abc",
        )
        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
            device.send_message("Hello world")
            p.assert_called_once_with(
                b"data.message=Hello+world&registration_id=abc",
                "application/x-www-form-urlencoded;charset=UTF-8")

    def test_gcm_send_message_extra(self):
        device = GCMDevice.objects.create(
            registration_id="abc",
        )
        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
            device.send_message("Hello world", extra={"foo": "bar"})
            p.assert_called_once_with(
                b"data.foo=bar&data.message=Hello+world&registration_id=abc",
                "application/x-www-form-urlencoded;charset=UTF-8")

    def test_gcm_send_message_collapse_key(self):
        device = GCMDevice.objects.create(
            registration_id="abc",
        )
        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
            device.send_message("Hello world", collapse_key="test_key")
            p.assert_called_once_with(
                b"collapse_key=test_key&data.message=Hello+world&registration_id=abc",
                "application/x-www-form-urlencoded;charset=UTF-8")

    def test_gcm_send_message_to_multiple_devices(self):
        GCMDevice.objects.create(
            registration_id="abc",
        )

        GCMDevice.objects.create(
            registration_id="abc1",
        )

        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE) as p:
            GCMDevice.objects.all().send_message("Hello world")
            p.assert_called_once_with(
                json.dumps({
                    "data": { "message": "Hello world" },
                    "registration_ids": ["abc", "abc1"]
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

    def test_gcm_send_message_active_devices(self):
        GCMDevice.objects.create(
            registration_id="abc",
            active=True
        )

        GCMDevice.objects.create(
            registration_id="xyz",
            active=False
        )

        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE) as p:
            GCMDevice.objects.all().send_message("Hello world")
            p.assert_called_once_with(
                json.dumps({
                    "data": { "message": "Hello world" },
                    "registration_ids": ["abc"]
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

    def test_gcm_send_message_extra_to_multiple_devices(self):
        GCMDevice.objects.create(
            registration_id="abc",
        )

        GCMDevice.objects.create(
            registration_id="abc1",
        )

        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE) as p:
            GCMDevice.objects.all().send_message("Hello world", extra={"foo": "bar"})
            p.assert_called_once_with(
                json.dumps({
                    "data": { "foo": "bar", "message": "Hello world" },
                    "registration_ids": ["abc", "abc1"]
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

    def test_gcm_send_message_collapse_to_multiple_devices(self):
        GCMDevice.objects.create(
            registration_id="abc",
        )

        GCMDevice.objects.create(
            registration_id="abc1",
        )

        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE) as p:
            GCMDevice.objects.all().send_message("Hello world", collapse_key="test_key")
            p.assert_called_once_with(
                json.dumps({
                    "collapse_key": "test_key",
                    "data": { "message": "Hello world" },
                    "registration_ids": ["abc", "abc1"]
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

    def test_gcm_send_message_to_single_device_with_error(self):
        # these errors are device specific, device.active will be set false
        device_list = ['abc', 'abc1']
        self.create_devices(device_list)
        for index, error in enumerate(GCM_PLAIN_RESPONSE_ERROR):
            with mock.patch("push_notifications.gcm._gcm_send",
                            return_value=error) as p:
                device = GCMDevice.objects. \
                    get(registration_id=device_list[index])
                device.send_message("Hello World!")
                assert GCMDevice.objects.get(registration_id=device_list[index]) \
                           .active is False

    def test_gcm_send_message_to_single_device_with_error_b(self):
        # these errors are not device specific, GCMError should be thrown
        device_list = ['abc']
        self.create_devices(device_list)
        with mock.patch("push_notifications.gcm._gcm_send",
                        return_value=GCM_PLAIN_RESPONSE_ERROR_B) as p:
            device = GCMDevice.objects. \
                get(registration_id=device_list[0])
            with self.assertRaises(GCMError):
                device.send_message("Hello World!")
            assert GCMDevice.objects.get(registration_id=device_list[0]) \
                            .active is True

    def test_gcm_send_message_to_multiple_devices_with_error(self):
        device_list = ['abc', 'abc1', 'abc2']
        self.create_devices(device_list)
        with mock.patch("push_notifications.gcm._gcm_send",
                        return_value=GCM_JSON_RESPONSE_ERROR) as p:
            devices = GCMDevice.objects.all()
            devices.send_message("Hello World")
            assert GCMDevice.objects.get(registration_id=device_list[0]) \
                       .active is False
            assert GCMDevice.objects.get(registration_id=device_list[1]) \
                       .active is True
            assert GCMDevice.objects.get(registration_id=device_list[2]) \
                       .active is False

    def test_apns_send_message(self):
        device = APNSDevice.objects.create(
            registration_id="abc",
        )
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_frame") as p:
            device.send_message("Hello world", socket=socket, expiration=1)
            p.assert_called_once_with("abc", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)

    def test_apns_send_message_extra(self):
        device = APNSDevice.objects.create(
            registration_id="abc",
        )
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_frame") as p:
            device.send_message("Hello world", extra={"foo": "bar"}, socket=socket, identifier=1, expiration=2, priority=5)
            p.assert_called_once_with("abc", b'{"aps":{"alert":"Hello world"},"foo":"bar"}', 1, 2, 5)

    def create_devices(self, devices):
        for device in devices:
            GCMDevice.objects.create(
                registration_id=device,
            )
