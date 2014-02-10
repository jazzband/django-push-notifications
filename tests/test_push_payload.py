import mock
from django.test import TestCase
from push_notifications.apns import _apns_send


class PushPayloadTest(TestCase):
    def test_push_payload(self):
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_message") as p:
            _apns_send('123', 'Hello world', badge=1, sound='chime', extra={"custom_data": 12345}, socket=socket)
            p.assert_called_once_with('123', {'aps': {'alert': 'Hello world', 'badge': 1, 'sound': 'chime'},
                                              "custom_data": 12345})
