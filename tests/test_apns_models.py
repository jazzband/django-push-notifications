import aioapns
import mock
import pytest
from aioapns.common import APNS_RESPONSE_CODE, NotificationResult
from django.conf import settings
from django.test import TestCase, override_settings

from push_notifications.exceptions import APNSError
from push_notifications.models import APNSDevice


class APNSModelTestCase(TestCase):

    def _create_devices(self, devices):
        for device in devices:
            print("created", device)
            APNSDevice.objects.create(registration_id=device)

    @pytest.fixture(autouse=True)
    def _apns_client(self):
        with mock.patch(
            "aioapns.APNs",
            **{
                "return_value.send_notification": mock.AsyncMock(
                    return_value=NotificationResult("xxx", APNS_RESPONSE_CODE.SUCCESS)
                ),
            }
        ) as mock_client_class:
            self.apns_client = mock_client_class.return_value
            yield
            del self.apns_client

    @override_settings()
    def test_apns_send_bulk_message(self):
        self._create_devices(["abc", "def"])

        # legacy conf manager requires a value
        settings.PUSH_NOTIFICATIONS_SETTINGS.update(
            {"APNS_CERTIFICATE": "/path/to/apns/certificate.pem"}
        )

        with mock.patch("time.time", return_value=0):
            APNSDevice.objects.all().send_message("Hello world", expiration=1)
        requests = {}
        for args, kwargs in self.apns_client.send_notification.call_args_list:
            assert not kwargs
            [request] = args
            requests[request.device_token] = request

        self.assertEqual(requests["abc"].message["aps"]["alert"], "Hello world")
        self.assertEqual(requests["def"].message["aps"]["alert"], "Hello world")
        self.assertEqual(requests["abc"].time_to_live, 1)

    def test_apns_send_message_extra(self):
        self._create_devices(["abc"])

        with mock.patch("time.time", return_value=0):
            APNSDevice.objects.get().send_message(
                "Hello world", expiration=2, priority=5, extra={"foo": "bar"}
            )
        args, kwargs = self.apns_client.send_notification.call_args
        [request] = args

        assert not kwargs
        self.assertEqual(request.device_token, "abc")
        self.assertEqual(request.message["aps"]["alert"], "Hello world")
        self.assertEqual(request.message["aps"]["custom"], {"foo": "bar"})
        self.assertEqual(str(request.priority), aioapns.PRIORITY_NORMAL)
        self.assertEqual(request.time_to_live, 2)

    def test_apns_send_message(self):
        self._create_devices(["abc"])
        with mock.patch("time.time", return_value=0):
            APNSDevice.objects.get().send_message("Hello world", expiration=1)
        args, kwargs = self.apns_client.send_notification.call_args
        [request] = args

        assert not kwargs
        assert request.device_token == "abc"
        assert request.message["aps"]["alert"] == "Hello world"
        assert request.time_to_live == 1

    def test_apns_send_message_to_single_device_with_error(self):
        # these errors are device specific, device.active will be set false
        devices = ["abc"]
        self._create_devices(devices)

        with mock.patch("push_notifications.apns._apns_send") as s:
            s.return_value = {"abc": "Unregistered"}
            device = APNSDevice.objects.get(registration_id="abc")
            with self.assertRaises(APNSError) as ae:
                device.send_message("Hello World!")
            self.assertEqual(ae.exception.status, "Unregistered")
            self.assertFalse(APNSDevice.objects.get(registration_id="abc").active)

    def test_apns_send_message_to_several_devices_with_error(self):
        # these errors are device specific, device.active will be set false
        devices = {"abc": "PayloadTooLarge", "def": "BadTopic", "ghi": "Unregistered"}
        self._create_devices(devices)

        with mock.patch("push_notifications.apns._apns_send") as s:

            for token, status in devices.items():
                s.return_value = {token: status}
                device = APNSDevice.objects.get(registration_id=token)
                with self.assertRaises(APNSError) as ae:
                    device.send_message("Hello World!")

                assert ae.exception.status == status
                if status == "Unregistered":
                    assert not APNSDevice.objects.get(registration_id=token).active
                else:
                    assert APNSDevice.objects.get(registration_id=token).active

    def test_apns_send_message_to_bulk_devices_with_error(self):
        # these errors are device specific, device.active will be set false
        results = {"abc": "PayloadTooLarge", "def": "BadTopic", "ghi": "Unregistered"}
        self._create_devices(results.keys())

        with mock.patch("push_notifications.apns._apns_send") as s:
            s.return_value = results

            APNSDevice.objects.all().send_message("Hello World!")

            for token, status in results.items():
                print(token)
                if status == "Unregistered":
                    assert not APNSDevice.objects.get(registration_id=token).active
                else:
                    assert APNSDevice.objects.get(registration_id=token).active
