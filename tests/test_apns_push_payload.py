import mock
import pytest
from aioapns import PRIORITY_HIGH
from aioapns.common import APNS_RESPONSE_CODE, NotificationResult
from django.test import TestCase

from push_notifications.apns import _apns_send
from push_notifications.exceptions import APNSUnsupportedPriority


class APNSPushPayloadTest(TestCase):
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

	def test_push_payload(self):
		with mock.patch("time.time", return_value=0):
			_apns_send(
				["123"],
				"Hello world",
				badge=1,
				sound="chime",
				extra={"custom_data": 12345},
				expiration=3,
			)

		self.apns_client.send_notification.assert_called_once()
		args, kwargs = self.apns_client.send_notification.call_args
		[request] = args

		assert not kwargs
		assert request.device_token == "123"
		assert request.message["aps"]["alert"] == "Hello world"
		assert request.message["aps"]["badge"] == 1
		assert request.message["aps"]["sound"] == "chime"
		assert request.message["aps"]["custom"] == {"custom_data": 12345}
		assert request.time_to_live == 3

	def test_push_payload_with_thread_id(self):
		with mock.patch("time.time", return_value=0):
			_apns_send(
				["123"],
				"Hello world",
				thread_id="565",
				sound="chime",
				extra={"custom_data": 12345},
				expiration=3,
			)
		args, kwargs = self.apns_client.send_notification.call_args
		[request] = args

		assert not kwargs
		assert request.device_token == "123"
		assert request.message["aps"]["alert"] == "Hello world"
		assert request.message["aps"]["thread_id"] == "565"
		assert request.message["aps"]["sound"] == "chime"
		assert request.message["aps"]["custom"] == {"custom_data": 12345}
		assert request.time_to_live == 3

	def test_push_payload_with_alert_dict(self):
		with mock.patch("time.time", return_value=0):
			_apns_send(
				["123"],
				alert={"title": "t1", "body": "b1"},
				sound="chime",
				extra={"custom_data": 12345},
				expiration=3,
			)
		args, kwargs = self.apns_client.send_notification.call_args
		[request] = args

		assert not kwargs
		assert request.device_token == "123"
		assert request.message["aps"]["alert"]["body"] == "b1"
		assert request.message["aps"]["alert"]["title"] == "t1"
		assert request.message["aps"]["sound"] == "chime"
		assert request.message["aps"]["custom"] == {"custom_data": 12345}
		assert request.time_to_live == 3

	def test_localised_push_with_empty_body(self):
		with mock.patch("time.time", return_value=0):
			_apns_send(["123"], None, loc_key="TEST_LOC_KEY", expiration=3)
		args, kwargs = self.apns_client.send_notification.call_args
		[request] = args

		assert not kwargs
		assert request.device_token == "123"
		assert request.message["aps"]["alert"]["body_localized_key"] == "TEST_LOC_KEY"
		assert request.time_to_live == 3

	def test_using_extra(self):
		with mock.patch("time.time", return_value=0):
			_apns_send(
				["123"], "sample", extra={"foo": "bar"}, expiration=30, priority=10
			)
		args, kwargs = self.apns_client.send_notification.call_args
		[request] = args

		assert not kwargs
		assert request.device_token == "123"
		assert request.message["aps"]["alert"] == "sample"
		assert request.message["aps"]["custom"] == {"foo": "bar"}
		assert str(request.priority) == PRIORITY_HIGH
		assert request.time_to_live == 30

	def test_collapse_id(self):
		_apns_send(["123"], "sample", collapse_id="456789")
		args, kwargs = self.apns_client.send_notification.call_args
		[request] = args

		assert not kwargs
		assert request.device_token == "123"
		assert request.message["aps"]["alert"], "sample"
		assert request.collapse_key == "456789"

	def test_bad_priority(self):
		with pytest.raises(APNSUnsupportedPriority):
			_apns_send(["123"], "_" * 2049, priority=24)
		self.apns_client.send_notification.assert_not_called()
