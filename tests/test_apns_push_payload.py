import mock
from django.test import TestCase
from push_notifications.apns import _apns_send, apns_fetch_inactive_ids, APNSDataOverflow
from push_notifications.models import APNSDevice

@mock.patch.dict("push_notifications.apns.SETTINGS",
                 {"APNS_HOST": "apns.host",
                  "APNS_PORT": 1234,
                  "APNS_FEEDBACK_HOST": "apns.feedback.host",
                  "APNS_FEEDBACK_PORT": 2345,
                  "APNS_CERTIFICATES": {"default": "default-cert",
                                        "app.id.0": "cert-0",
                                        "app.id.1": "cert-1"}})
class APNSPushPayloadTest(TestCase):
	def test_push_payload(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send("123", "Hello world",
				badge=1, sound="chime", extra={"custom_data": 12345}, expiration=3, socket=socket)
			p.assert_called_once_with("123",
				b'{"aps":{"alert":"Hello world","badge":1,"sound":"chime"},"custom_data":12345}', 0, 3, 10)

	def test_localised_push_with_empty_body(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send("123", None, loc_key="TEST_LOC_KEY", expiration=3, socket=socket)
			p.assert_called_once_with("123", b'{"aps":{"alert":{"loc-key":"TEST_LOC_KEY"}}}', 0, 3, 10)

	def test_using_extra(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
                        _apns_send("123", "sample", extra={"foo": "bar"}, identifier=10, expiration=30, priority=10, socket=socket)
                        p.assert_called_once_with("123", b'{"aps":{"alert":"sample"},"foo":"bar"}', 10, 30, 10)

	def test_oversized_payload(self):
		socket = mock.MagicMock()
                with mock.patch("push_notifications.apns._apns_pack_frame") as p:
                        self.assertRaises(APNSDataOverflow, _apns_send, "123", "_" * 2049, socket=socket)
			p.assert_has_calls([])

        def test_cert_selection(self):
                with mock.patch("push_notifications.apns._apns_create_socket") as create_socket:
                        d = APNSDevice(registration_id="1234")
                        d.send_message("sample")
                        create_socket.assert_called_once_with(("apns.host", 1234), 'default-cert')

                with mock.patch("push_notifications.apns._apns_create_socket") as create_socket:
                        d = APNSDevice(registration_id="1234", app_id="app.id.0")
                        d.send_message("sample")
                        create_socket.assert_called_once_with(("apns.host", 1234), 'cert-0')

                with mock.patch("push_notifications.apns._apns_create_socket") as create_socket:
                        d = APNSDevice(registration_id="1234", app_id="app.id.1")
                        d.send_message("sample")
                        create_socket.assert_called_once_with(("apns.host", 1234), 'cert-1')

        def test_feedback_across_all_apps(self):
                def mock_create_socket(address_tuple, certfile):
                        socket = mock.Mock()
                        socket.certfile = certfile
                        return socket

                def mock_receive_feedback(socket):
                        return [('fake-tstamp', socket.certfile + '.0'),
                                ('fake-tstamp', socket.certfile + '.1')]

                with mock.patch("push_notifications.apns._apns_create_socket", mock_create_socket):
                        with mock.patch("push_notifications.apns._apns_receive_feedback", mock_receive_feedback):
                                self.assertItemsEqual([id.decode('hex') for id in apns_fetch_inactive_ids()],
                                                      ['default-cert.0', 'default-cert.1',
                                                       'cert-0.0', 'cert-0.1',
                                                       'cert-1.0', 'cert-1.1'])

