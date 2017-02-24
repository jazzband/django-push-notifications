
import os
from django.test import TestCase
from push_notifications.apns import _apns_send, APNSDataOverflow
from ._mock import mock

from django.conf import settings
from push_notifications.models import ApplicationModel

class APNSPushPayloadTest(TestCase):
	def test_push_payload(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send("123", "Hello world", None,
				badge=1, sound="chime", extra={"custom_data": 12345}, expiration=3, socket=socket)
			p.assert_called_once_with(
				"123", b'{"aps":{"alert":"Hello world","badge":1,"sound":"chime"},"custom_data":12345}',
				0, 3, 10
			)


	def test_push_payload_with_thread_id(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send(
				"123", "Hello world", thread_id="565", sound="chime",
				extra={"custom_data": 12345}, expiration=3, socket=socket
			)
			p.assert_called_once_with(
				"123",
				b'{"aps":{"alert":"Hello world","sound":"chime","thread-id":"565"},"custom_data":12345}',
				0, 3, 10)

	def test_push_payload_with_alert_dict(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send(
				"123", alert={'title':'t1', 'body':'b1'}, sound="chime",
				extra={"custom_data": 12345}, expiration=3, socket=socket
			)
			p.assert_called_once_with(
				"123",
				b'{"aps":{"alert":{"body":"b1","title":"t1"},"sound":"chime"},"custom_data":12345}',
				0, 3, 10)

	def test_localised_push_with_empty_body(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send("123", None, None, loc_key="TEST_LOC_KEY", expiration=3, socket=socket)
			p.assert_called_once_with(
				"123",
				b'{"aps":{"alert":{"loc-key":"TEST_LOC_KEY"}}}', 0, 3, 10
			)

	def test_using_extra(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			_apns_send(
				"123", "sample", None, extra={"foo": "bar"},
				identifier=10, expiration=30, priority=10, socket=socket
			)
			p.assert_called_once_with(
				"123", 
				b'{"aps":{"alert":"sample"},"foo":"bar"}', 10, 30, 10
			)

	def test_oversized_payload(self):
		socket = mock.MagicMock()
		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			self.assertRaises(APNSDataOverflow, _apns_send, "123", "_" * 2049, None, socket=socket)
			p.assert_has_calls([])

class APNSPushSettingsTest(TestCase):
	def test_push_payload_with_app_id(self):
		settings.PUSH_NOTIFICATIONS_SETTINGS['APNS_CERTIFICATES_MODEL'] = {
		    'model':'push_notifications.ApplicationModel',
		    'key':'application_id',
		    'value':'apns_certificate',
		}
		import ssl
		from django.core.files.base import ContentFile
		path = os.path.join(os.path.dirname(__file__),"test_data","good_revoked.pem")
		f = open(path,'r')
		content = f.read()
		f.close()
		f = ContentFile(content)
		a = ApplicationModel.objects.create(application_id='qwertyxxx')
		a.apns_certificate.save("uiopcertxxx",f)
		path = a.apns_certificate.path
		socket = mock.MagicMock()
		with mock.patch("ssl.wrap_socket",return_value=socket) as s:
			with mock.patch("push_notifications.apns._apns_pack_frame") as p:
				_apns_send("123", "Hello world", 'qwertyxxx',
					badge=1, sound="chime", extra={"custom_data": 12345}, expiration=3)
				s.assert_called_once_with(*s.call_args[0],ca_certs=None,certfile=path,ssl_version=ssl.PROTOCOL_TLSv1)
				p.assert_called_once_with("123",
					b'{"aps":{"alert":"Hello world","badge":1,"sound":"chime"},"custom_data":12345}', 0, 3, 10)
	def tearDown(self):
	    # teardown temporary media
	    from django.conf import settings
	    import os
	    for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False):
	        for name in files:
	            os.remove(os.path.join(root, name))
	        for name in dirs:
	            os.rmdir(os.path.join(root, name))
	    os.removedirs(settings.MEDIA_ROOT)
