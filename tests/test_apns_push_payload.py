import mock
from django.test import TestCase
from push_notifications.apns import _apns_send, APNSDataOverflow


class APNSPushPayloadTest(TestCase):
    def test_push_payload(self):
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_message") as p:
            _apns_send('123', 'Hello world', badge=1, sound='chime', extra={"custom_data": 12345}, socket=socket)
            p.assert_called_once_with('123', '{"aps":{"sound":"chime","badge":1,"alert":"Hello world"},'
                                             '"custom_data":12345}')

    def test_localised_push_with_empty_body(self):
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_message") as p:
            _apns_send('123', None, loc_key='TEST_LOC_KEY', socket=socket)
            p.assert_called_once_with('123', '{"aps":{"alert":{"loc-key":"TEST_LOC_KEY"}}}')

    def test_using_extra(self):
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_message") as p:
            _apns_send('123', 'sample', extra={"foo": "bar"}, socket=socket)
            p.assert_called_once_with('123', '{"aps":{"alert":"sample"},"foo":"bar"}')

    def test_oversized_payload(self):
        socket = mock.MagicMock()
        with mock.patch("push_notifications.apns._apns_pack_message") as p:
            self.assertRaises(APNSDataOverflow, _apns_send, '123', '_' * 257, socket=socket)
            p.assert_has_calls([])
