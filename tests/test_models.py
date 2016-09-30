import json
from django.test import TestCase
from django.utils import timezone
from push_notifications.gcm import GCMError, gcm_send_bulk_message
from push_notifications.models import GCMDevice, APNSDevice
from ._mock import mock


# Mock responses

GCM_PLAIN_RESPONSE = "id=1:08"
GCM_JSON_RESPONSE = '{"multicast_id":108,"success":1,"failure":0,"canonical_ids":0,"results":[{"message_id":"1:08"}]}'
GCM_MULTIPLE_JSON_RESPONSE = (
	'{"multicast_id":108,"success":2,"failure":0,"canonical_ids":0,"results":'
	'[{"message_id":"1:08"}, {"message_id": "1:09"}]}'
)
GCM_JSON_RESPONSE_ERROR = (
	'{"success":1, "failure": 2, "canonical_ids": 0, "cast_id": 6358665107659088804, "results":'
	' [{"error": "NotRegistered"}, {"message_id": "0:1433830664381654%3449593ff9fd7ecd"}, '
	'{"error": "InvalidRegistration"}]}'
)
GCM_JSON_RESPONSE_ERROR_B = (
	'{"success":1, "failure": 2, "canonical_ids": 0, "cast_id": 6358665107659088804, '
	'"results": [{"error": "MismatchSenderId"}, {"message_id": '
	'"0:1433830664381654%3449593ff9fd7ecd"}, {"error": "InvalidRegistration"}]}'
)
GCM_JSON_CANONICAL_ID_RESPONSE = (
	'{"failure":0,"canonical_ids":1,"success":2,"multicast_id":7173139966327257000,"results":'
	'[{"registration_id":"NEW_REGISTRATION_ID","message_id":"0:1440068396670935%6868637df9fd7ecd"},'
	'{"message_id":"0:1440068396670937%6868637df9fd7ecd"}]}'
)
GCM_JSON_CANONICAL_ID_SAME_DEVICE_RESPONSE = (
	'{"failure":0,"canonical_ids":1,"success":2,"multicast_id":7173139966327257000,'
	'"results":[{"registration_id":"bar","message_id":"0:1440068396670935%6868637df9fd7ecd"}'
	',{"message_id":"0:1440068396670937%6868637df9fd7ecd"}]}'
)


class ModelTestCase(TestCase):
	def _create_devices(self, devices):
		for device in devices:
			GCMDevice.objects.create(registration_id=device)

	def test_can_save_gcm_device(self):
		device = GCMDevice.objects.create(registration_id="a valid registration id")
		assert device.id is not None
		assert device.date_created is not None
		assert device.date_created.date() == timezone.now().date()

	def test_can_create_save_device(self):
		device = APNSDevice.objects.create(registration_id="a valid registration id")
		assert device.id is not None
		assert device.date_created is not None
		assert device.date_created.date() == timezone.now().date()

	def test_gcm_send_message(self):
		device = GCMDevice.objects.create(registration_id="abc")
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE
		) as p:
				device.send_message("Hello world")
				p.assert_called_once_with(
					b"data.message=Hello+world&registration_id=abc",
					"application/x-www-form-urlencoded;charset=UTF-8"
				)

	def test_gcm_send_message_extra(self):
		device = GCMDevice.objects.create(registration_id="abc")
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE
		) as p:
			device.send_message("Hello world", extra={"foo": "bar"})
			p.assert_called_once_with(
				b"data.foo=bar&data.message=Hello+world&registration_id=abc",
				"application/x-www-form-urlencoded;charset=UTF-8"
			)

	def test_gcm_send_message_collapse_key(self):
		device = GCMDevice.objects.create(registration_id="abc")
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_PLAIN_RESPONSE
		) as p:
			device.send_message("Hello world", collapse_key="test_key")
			p.assert_called_once_with(
				b"collapse_key=test_key&data.message=Hello+world&registration_id=abc",
				"application/x-www-form-urlencoded;charset=UTF-8"
			)

	def test_gcm_send_message_to_multiple_devices(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"data": {"message": "Hello world"},
					"registration_ids": ["abc", "abc1"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

	def test_gcm_send_message_active_devices(self):
		GCMDevice.objects.create(registration_id="abc", active=True)
		GCMDevice.objects.create(registration_id="xyz", active=False)

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE
		) as p:
			GCMDevice.objects.all().send_message("Hello world")
			p.assert_called_once_with(
				json.dumps({
					"data": {"message": "Hello world"},
					"registration_ids": ["abc"]
				}, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

	def test_gcm_send_message_collapse_to_multiple_devices(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_MULTIPLE_JSON_RESPONSE
		) as p:
				GCMDevice.objects.all().send_message("Hello world", collapse_key="test_key")
				p.assert_called_once_with(
					json.dumps({
						"collapse_key": "test_key",
						"data": {"message": "Hello world"},
						"registration_ids": ["abc", "abc1"]
					}, separators=(",", ":"), sort_keys=True).encode("utf-8"), "application/json")

	def test_gcm_send_message_to_single_device_with_error(self):
		# these errors are device specific, device.active will be set false
		devices = ["abc", "abc1"]
		self._create_devices(devices)

		errors = ["Error=NotRegistered", "Error=InvalidRegistration"]
		for index, error in enumerate(errors):
			with mock.patch(
				"push_notifications.gcm._gcm_send", return_value=error):
				device = GCMDevice.objects.get(registration_id=devices[index])
				device.send_message("Hello World!")
				assert GCMDevice.objects.get(registration_id=devices[index]).active is False

	def test_gcm_send_message_to_single_device_with_error_b(self):
		device = GCMDevice.objects.create(registration_id="abc")

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value="Error=MismatchSenderId"
		):
			# these errors are not device specific, GCMError should be thrown
			with self.assertRaises(GCMError):
				device.send_message("Hello World!")
			assert GCMDevice.objects.get(registration_id="abc").active is True

	def test_gcm_send_message_to_multiple_devices_with_error(self):
		self._create_devices(["abc", "abc1", "abc2"])
		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_JSON_RESPONSE_ERROR
		):
			devices = GCMDevice.objects.all()
			devices.send_message("Hello World")
			assert not GCMDevice.objects.get(registration_id="abc").active
			assert GCMDevice.objects.get(registration_id="abc1").active
			assert not GCMDevice.objects.get(registration_id="abc2").active

	def test_gcm_send_message_to_multiple_devices_with_error_b(self):
		self._create_devices(["abc", "abc1", "abc2"])

		with mock.patch(
			"push_notifications.gcm._gcm_send", return_value=GCM_JSON_RESPONSE_ERROR_B
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
			"push_notifications.gcm._gcm_send", return_value=GCM_JSON_CANONICAL_ID_RESPONSE
		):
			GCMDevice.objects.all().send_message("Hello World")
			assert not GCMDevice.objects.filter(registration_id="foo").exists()
			assert GCMDevice.objects.filter(registration_id="bar").exists()
			assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists() is True

	def test_gcm_send_message_to_single_user_with_canonical_id(self):
		old_registration_id = "foo"
		self._create_devices([old_registration_id])

		gcm_reg_blob = "id=1:2342\nregistration_id=NEW_REGISTRATION_ID"
		with mock.patch("push_notifications.gcm._gcm_send", return_value=gcm_reg_blob):
			GCMDevice.objects.get(registration_id=old_registration_id).send_message("Hello World")
			assert not GCMDevice.objects.filter(registration_id=old_registration_id).exists()
			assert GCMDevice.objects.filter(registration_id="NEW_REGISTRATION_ID").exists()

	def test_gcm_send_message_to_same_devices_with_canonical_id(self):
		first_device = GCMDevice.objects.create(registration_id="foo", active=True)
		second_device = GCMDevice.objects.create(registration_id="bar", active=False)

		with mock.patch(
			"push_notifications.gcm._gcm_send",
			return_value=GCM_JSON_CANONICAL_ID_SAME_DEVICE_RESPONSE
		):
			GCMDevice.objects.all().send_message("Hello World")

		assert first_device.active is True
		assert second_device.active is False

	def test_apns_send_message(self):
		device = APNSDevice.objects.create(registration_id="abc")
		socket = mock.MagicMock()

		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			device.send_message("Hello world", socket=socket, expiration=1)
			p.assert_called_once_with("abc", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)

	def test_apns_send_message_extra(self):
		device = APNSDevice.objects.create(registration_id="abc")
		socket = mock.MagicMock()

		with mock.patch("push_notifications.apns._apns_pack_frame") as p:
			device.send_message(
				"Hello world", extra={"foo": "bar"}, socket=socket,
				identifier=1, expiration=2, priority=5
			)
			p.assert_called_once_with("abc", b'{"aps":{"alert":"Hello world"},"foo":"bar"}', 1, 2, 5)

	def test_send_message_with_no_reg_ids(self):
		self._create_devices(["abc", "abc1"])

		with mock.patch("push_notifications.gcm._gcm_send_plain", return_value="") as p:
			GCMDevice.objects.filter(registration_id="xyz").send_message("Hello World")
			p.assert_not_called()

		with mock.patch("push_notifications.gcm._gcm_send_json", return_value="") as p:
			reg_ids = [obj.registration_id for obj in GCMDevice.objects.all()]
			gcm_send_bulk_message(reg_ids, {"message": "Hello World"})
			p.assert_called_once_with([u"abc", u"abc1"], {"message": "Hello World"})

	def test_can_save_wsn_device(self):
		device = GCMDevice.objects.create(registration_id="a valid registration id")
		self.assertIsNotNone(device.pk)
		self.assertIsNotNone(device.date_created)
		self.assertEqual(device.date_created.date(), timezone.now().date())

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


class APNSModelWithSettingsTestCase(TestCase):
	def test_apns_send_message_with_app_id(self):
		from django.conf import settings
		device = APNSDevice.objects.create(
			registration_id="abc",
			application_id="asdfg"
		)
		settings.PUSH_NOTIFICATIONS_SETTINGS['APNS_CERTIFICATES'] = {
			'asdfg': 'uiopcert'
		}
		f = open('uiopcert', 'wb')
		f.write(b'')
		f.close()
		import ssl
		socket = mock.MagicMock()
		with mock.patch("ssl.wrap_socket", return_value=socket) as s:
			with mock.patch("push_notifications.apns._apns_pack_frame") as p:
				device.send_message("Hello world", expiration=1)
				p.assert_called_once_with("abc", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)
				s.assert_called_once_with(
					*s.call_args[0], ca_certs=None, certfile='uiopcert',
					ssl_version=ssl.PROTOCOL_TLSv1
				)

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
			'asdfg': 'uiopcert'
		}
		f = open('uiopcert', 'wb')
		f.write(b'')
		f.close()
		import ssl
		socket = mock.MagicMock()
		with mock.patch("ssl.wrap_socket", return_value=socket) as s:
			with mock.patch("push_notifications.apns._apns_pack_frame") as p:
				APNSDevice.objects.all().send_message("Hello world", expiration=1)
				device.send_message("Hello world", expiration=1)
				p.assert_any_call("abc", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)
				p.assert_any_call("def", b'{"aps":{"alert":"Hello world"}}', 0, 1, 10)
				s.assert_any_call(
					*s.call_args_list[0][0],
					ca_certs=None,
					certfile='uiopcert',
					ssl_version=ssl.PROTOCOL_TLSv1
				)

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
			'asdfg': 'uiopkey'
		}
		with mock.patch("push_notifications.gcm.urlopen") as u:
			device.send_message("Hello world")
			request = u.call_args[0][0]
			assert request.headers['Authorization'] == 'key=uiopkey'

	def test_gcm_send_multi_message_with_app_id(self):
		from django.conf import settings
		settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEYS'] = {
			'asdfg': 'uiopkey'
		}
		try:
			from StringIO import StringIO
		except ImportError:
			from io import StringIO
		import json
		with mock.patch("push_notifications.gcm.urlopen", return_value=StringIO(json.dumps({
			'failure': [],
			'canonical_ids': []
		}))) as u:
			GCMDevice.objects.all().send_message("Hello world")
			assert u.call_count == 1
			request = u.call_args[0][0]
			assert request.headers['Authorization'] == 'key=uiopkey'

	def test_gcm_send_multi_message_with_different_app_id(self):
		from django.conf import settings
		settings.PUSH_NOTIFICATIONS_SETTINGS['GCM_API_KEYS'] = {
			'asdfg': 'asdfgkey',
			'uiop': 'uiopkey'
		}
		try:
			from StringIO import StringIO
		except ImportError:
			from io import StringIO
		import json
		requests = []

		def c():
			def f(r):
				requests.append(r)
				return StringIO(json.dumps({
					'failure': [],
					'canonical_ids': []
				}))
			return f
		with mock.patch("push_notifications.gcm.urlopen", new_callable=c):
			GCMDevice.objects.all().send_message("Hello world")
			keys = set(r.headers['Authorization'] for r in requests)
			assert len(keys) == 2
			assert 'key=asdfgkey' in keys
			assert 'key=uiopkey' in keys
