import json
import mock
from django.test import TestCase
from django.utils import timezone
from push_notifications.models import GCMDevice, APNSDevice
from tests.mock_responses import GCM_PLAIN_RESPONSE, \
    GCM_MULTIPLE_JSON_RESPONSE, GCM_PLAIN_RESPONSE_ERROR, \
    GCM_JSON_RESPONSE_ERROR, GCM_PLAIN_RESPONSE_ERROR_B,\
    GCM_PLAIN_CANONICAL_ID_RESPONSE, GCM_JSON_CANONICAL_ID_RESPONSE,\
    GCM_JSON_CANONICAL_ID_SAME_DEVICE_RESPONSE
from push_notifications.gcm import GCMError

from contextlib import nested

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
                "application/x-www-form-urlencoded;charset=UTF-8",
                None)

    def test_gcm_send_message_with_app_id(self):
        device = GCMDevice.objects.create(
            registration_id="abc",
            application_id="qwerty",
        )
        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
            device.send_message("Hello world")
            p.assert_called_once_with(
                b"data.message=Hello+world&registration_id=abc",
                "application/x-www-form-urlencoded;charset=UTF-8",
                "qwerty")

    def test_gcm_send_message_extra(self):
        device = GCMDevice.objects.create(
            registration_id="abc",
        )
        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
            device.send_message("Hello world", extra={"foo": "bar"})
            p.assert_called_once_with(
                b"data.foo=bar&data.message=Hello+world&registration_id=abc",
                "application/x-www-form-urlencoded;charset=UTF-8",
                None)

    def test_gcm_send_message_collapse_key(self):
        device = GCMDevice.objects.create(
            registration_id="abc",
        )
        with mock.patch("push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE) as p:
            device.send_message("Hello world", collapse_key="test_key")
            p.assert_called_once_with(
                b"collapse_key=test_key&data.message=Hello+world&registration_id=abc",
                "application/x-www-form-urlencoded;charset=UTF-8",
                None)

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
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json",None)

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
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json",None)

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
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json",None)

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
                }, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json",None)

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

    def test_gcm_send_message_to_multiple_devices_with_canonical_id(self):
        device_list = ['foo', 'bar']
        self.create_devices(device_list)
        with mock.patch("push_notifications.gcm._gcm_send",
                        return_value=GCM_JSON_CANONICAL_ID_RESPONSE):
            GCMDevice.objects.all().send_message("Hello World")
            assert GCMDevice.objects.filter(registration_id=device_list[0]).exists() is False
            assert GCMDevice.objects.filter(registration_id=device_list[1]).exists() is True
            assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists() is True

    def test_gcm_send_message_to_single_user_with_canonical_id(self):
        old_registration_id = 'foo'
        self.create_devices([old_registration_id])
        with mock.patch("push_notifications.gcm._gcm_send",
                        return_value=GCM_PLAIN_CANONICAL_ID_RESPONSE):
            GCMDevice.objects.get(registration_id=old_registration_id).send_message("Hello World")
            assert GCMDevice.objects.filter(registration_id=old_registration_id).exists() is False
            assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists() is True

    def test_gcm_send_message_to_same_devices_with_canonical_id(self):
        device_list = ['foo', 'bar']
        self.create_devices(device_list)
        first_device_pk = GCMDevice.objects.get(registration_id='foo').pk
        second_device_pk = GCMDevice.objects.get(registration_id='bar').pk
        with mock.patch("push_notifications.gcm._gcm_send",
                        return_value=GCM_JSON_CANONICAL_ID_SAME_DEVICE_RESPONSE):
            GCMDevice.objects.all().send_message("Hello World")
        first_device = GCMDevice.objects.get(pk=first_device_pk)
        second_device = GCMDevice.objects.get(pk=second_device_pk)
        assert first_device.active is False
        assert second_device.active is True

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

class APNSModelWithSettingsTestCase(TestCase):
    def test_apns_send_message_with_app_id(self):
        from django.conf import settings
        device = APNSDevice.objects.create(
            registration_id="abc",
            application_id="asdfg"
        )
        settings.PUSH_NOTIFICATIONS_SETTINGS['APNS_CERTIFICATES'] = {
            'asdfg':'uiopcert'
        }
        f = open('uiopcert','wb')
        f.write('')
        f.close()
        import ssl
        socket = mock.MagicMock()
        with nested(
            mock.patch("ssl.wrap_socket",return_value=socket),
            mock.patch("push_notifications.apns._apns_pack_frame"),
        ) as (s,p):
            device.send_message("Hello world", expiration=1)
            p.assert_called_once_with("abc", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)
            s.assert_called_once_with(*s.call_args[0],ca_certs=None,certfile='uiopcert',ssl_version=ssl.PROTOCOL_TLSv1)

    def test_apns_send_multi_message_with_app_id(self):
        from django.conf import settings
        device = APNSDevice.objects.create(
            registration_id="abc",
            application_id="asdfg"
        )
        device = APNSDevice.objects.create(
            registration_id="def",
            application_id="asdfg"
        )
        settings.PUSH_NOTIFICATIONS_SETTINGS['APNS_CERTIFICATES'] = {
            'asdfg':'uiopcert'
        }
        f = open('uiopcert','wb')
        f.write('')
        f.close()
        import ssl
        socket = mock.MagicMock()
        with nested(
            mock.patch("ssl.wrap_socket",return_value=socket),
            mock.patch("push_notifications.apns._apns_pack_frame"),
        ) as (s,p):
            APNSDevice.objects.all().send_message("Hello world", expiration=1)
            device.send_message("Hello world", expiration=1)
            p.assert_any_call("abc", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)
            p.assert_any_call("def", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)
            s.assert_any_call(*s.call_args_list[0][0],ca_certs=None,certfile='uiopcert',ssl_version=ssl.PROTOCOL_TLSv1)

    def tearDown(self):
        import os
        os.unlink('uiopcert')

class GCMModelWithSettingsTestCase(TestCase):
    def test_gcm_send_message_with_app_id(self):
        from django.conf import settings
        device = GCMDevice.objects.create(
            registration_id="abc",
            application_id="asdfg"
        )
        settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEYS'] = {
            'asdfg':'uiopkey'
        }
        with mock.patch("push_notifications.gcm.urlopen") as u:
            device.send_message("Hello world")
            request = u.call_args[0][0]
            assert request.headers['Authorization'] == 'key=uiopkey'

    def test_gcm_send_multi_message_with_app_id(self):
        from django.conf import settings
        device = GCMDevice.objects.create(
            registration_id="abc",
            application_id="asdfg"
        )
        device = GCMDevice.objects.create(
            registration_id="def",
            application_id="asdfg"
        )
        settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEYS'] = {
            'asdfg':'uiopkey'
        }
        from StringIO import StringIO
        import json
        with mock.patch("push_notifications.gcm.urlopen",return_value=StringIO(json.dumps({
            'failure':[],
            'canonical_ids':[]
        }))) as u:
            GCMDevice.objects.all().send_message("Hello world")
            assert u.call_count == 1
            request = u.call_args[0][0]
            assert request.headers['Authorization'] == 'key=uiopkey'

    def test_gcm_send_multi_message_with_different_app_id(self):
        from django.conf import settings
        device = GCMDevice.objects.create(
            registration_id="abc",
            application_id="asdfg"
        )
        device = GCMDevice.objects.create(
            registration_id="def",
            application_id="uiop"
        )
        settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEYS'] = {
            'asdfg':'asdfgkey',
            'uiop':'uiopkey'
        }
        from StringIO import StringIO
        import json
        requests = []
        def c():
            def f(r):
                requests.append(r)
                return StringIO(json.dumps({
                    'failure':[],
                    'canonical_ids':[]
                }))
            return f
        with mock.patch("push_notifications.gcm.urlopen",new_callable=c) as u:
            GCMDevice.objects.all().send_message("Hello world")
            keys = set(r.headers['Authorization'] for r in requests)
            assert len(keys) == 2
            assert 'key=asdfgkey' in keys
            assert 'key=uiopkey' in keys
