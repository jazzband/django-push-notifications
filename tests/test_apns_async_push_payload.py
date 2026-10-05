import sys
import time
from unittest import mock

import pytest
from django.test import TestCase

from push_notifications.models import APNSDevice


try:
	from aioapns.common import NotificationResult
	from push_notifications.apns_async import (
		apns_send_bulk_message, apns_send_message, BulkNotificationResult,
		CertificateCredentials, TokenCredentials,
	)
except ModuleNotFoundError:
	# skipping because apns2 is not supported on python 3.10
	# it uses hyper that imports from collections which were changed in 3.10
	# and we would get  "AttributeError: module 'collections' has no attribute 'MutableMapping'"
	if sys.version_info < (3, 10):
		pytest.skip(allow_module_level=True)
	else:
		raise


class APNSAsyncPushPayloadTest(TestCase):
	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
			badge=1,
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)
		self.assertTrue(mock_apns.called)
		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]
		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "Hello world")
		self.assertEqual(req.message["aps"]["badge"], 1)
		self.assertEqual(req.message["aps"]["sound"], "chime")
		self.assertEqual(req.message["custom_data"], 12345)
		self.assertEqual(req.time_to_live, 3)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_thread_id(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			thread_id="565",
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
		)
		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "Hello world")
		self.assertEqual(req.message["aps"]["thread-id"], "565")
		self.assertEqual(req.message["aps"]["sound"], "chime")
		self.assertEqual(req.message["custom_data"], 12345)
		self.assertAlmostEqual(req.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_alert_dict(self, mock_apns):
		apns_send_message(
			"123",
			alert={"title": "t1", "body": "b1"},
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"]["body"], "b1")
		self.assertEqual(req.message["aps"]["alert"]["title"], "t1")
		self.assertEqual(req.message["aps"]["sound"], "chime")
		self.assertEqual(req.message["custom_data"], 12345)
		self.assertAlmostEqual(req.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_localised_push_with_empty_body(self, mock_apns):
		apns_send_message(
			"123",
			None,
			loc_key="TEST_LOC_KEY",
			expiration=time.time() + 3,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, _kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"]["loc-key"], "TEST_LOC_KEY")
		self.assertAlmostEqual(req.time_to_live, 3, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_using_extra(self, mock_apns):
		apns_send_message(
			"123",
			"sample",
			extra={"foo": "bar"},
			expiration=(time.time() + 30),
			priority=10,
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, _kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "sample")
		self.assertEqual(req.message["foo"], "bar")
		self.assertEqual(req.priority, 10)
		self.assertAlmostEqual(req.time_to_live, 30, places=-1)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_collapse_id(self, mock_apns):
		apns_send_message(
			"123",
			"sample",
			collapse_id="456789",
			creds=TokenCredentials(
				key="aaa",
				key_id="bbb",
				team_id="ccc",
			),
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		self.assertEqual(req.device_token, "123")
		self.assertEqual(req.message["aps"]["alert"], "sample")
		self.assertEqual(req.collapse_key, "456789")

	@mock.patch("aioapns.client.APNsCertConnectionPool", autospec=True)
	def test_aioapns_err_func(self, mock_cert_pool):
		mock_cert_pool.return_value.send_notification = mock.AsyncMock()
		result = NotificationResult("123", "400", description="BadDeviceToken")
		mock_cert_pool.return_value.send_notification.return_value = result
		err_func = mock.AsyncMock()

		response = apns_send_message(
			"123",
			"sample",
			creds=CertificateCredentials(
				client_cert="dummy/path.pem",
			),
			topic="default",
			err_func=err_func,
		)

		self.assertEqual(response, {"results": [{"error": "BadDeviceToken"}]})
		mock_cert_pool.assert_called_once()
		mock_cert_pool.return_value.send_notification.assert_called_once()
		mock_cert_pool.return_value.send_notification.assert_awaited_once()
		err_func.assert_called_with(
			mock.ANY, result
		)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_mutable_content(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			mutable_content=True,
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		# Assertions
		self.assertTrue("mutable-content" in req.message["aps"])
		self.assertEqual(req.message["aps"]["mutable-content"], 1)  # APNs expects 1 for True

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_category(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			category="MESSAGE_CATEGORY",
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
			sound="chime",
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		# Assertions
		self.assertTrue("category" in req.message["aps"])
		self.assertEqual(req.message["aps"]["category"], "MESSAGE_CATEGORY")  # Verify correct category value

	# def test_bad_priority(self):
	# 	with mock.patch("apns2.credentials.init_context"):
	# 		with mock.patch("apns2.client.APNsClient.connect"):
	# 			with mock.patch("apns2.client.APNsClient.send_notification") as s:
	# 				self.assertRaises(APNSUnsupportedPriority, _apns_send, "123",
	# 				 "_" * 2049, priority=24)
	# 			s.assert_has_calls([])

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_content_available_bool_true(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			content_available=True,
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		assert "content-available" in req.message["aps"]
		assert req.message["aps"]["content-available"] == 1


	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_content_available_bool_false(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			content_available=False,
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		assert "content-available" not in req.message["aps"]


	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_push_payload_with_content_available_not_set(self, mock_apns):
		apns_send_message(
			"123",
			"Hello world",
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
			extra={"custom_data": 12345},
			expiration=int(time.time()) + 3,
		)

		args, kwargs = mock_apns.return_value.send_notification.call_args
		req = args[0]

		assert "content-available" not in req.message["aps"]


class APNSAsyncBulkMessageErrorHandlingTest(TestCase):
	def _bulk_send(self, mock_apns, responses):
		registration_ids = ["token{}".format(idx) for idx in range(1, len(responses) + 1)]
		mock_apns.return_value.send_notification.side_effect = [
			NotificationResult(
				notification_id=registration_id,
				status=status,
				description=description,
			)
			for registration_id, (status, description) in zip(registration_ids, responses)
		]
		return apns_send_bulk_message(
			registration_ids=registration_ids,
			alert="Hello world",
			creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
		)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_reports_per_registration_id_errors_without_raising(self, mock_apns):
		scenarios = [
			(
				"all delivered",
				[("200", None), ("200", None)],
				{"token1": "Success", "token2": "Success"},
				[],
			),
			(
				"one rejected token",
				[("200", None), ("400", "BadDeviceToken")],
				{"token1": "Success", "token2": "BadDeviceToken"},
				[("token2", "BadDeviceToken")],
			),
			(
				"several failures",
				[
					("400", "Unregistered"),
					("400", "DeviceTokenNotForTopic"),
					("failed", "TimeoutError"),
				],
				{
					"token1": "Unregistered",
					"token2": "DeviceTokenNotForTopic",
					"token3": "TimeoutError",
				},
				[
					("token1", "Unregistered"),
					("token2", "DeviceTokenNotForTopic"),
					("token3", "TimeoutError"),
				],
			),
		]

		for name, responses, expected_results, expected_errors in scenarios:
			with self.subTest(name):
				result = self._bulk_send(mock_apns, responses)

				self.assertIsInstance(result, BulkNotificationResult)
				self.assertEqual(result.results, expected_results)
				self.assertEqual(result.has_errors, bool(expected_errors))
				self.assertEqual(
					result.errors,
					[
						{
							"registration_id": registration_id,
							"error_type": error_type,
							"error_message": error_type,
							"timestamp": mock.ANY,
						}
						for registration_id, error_type in expected_errors
					],
				)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_deactivates_only_permanently_rejected_registration_ids(self, mock_apns):
		for registration_id in ["token1", "token2", "token3"]:
			APNSDevice.objects.create(registration_id=registration_id)

		scenarios = [
			("unregistered", ["Unregistered", "DeviceTokenNotForTopic"], False, False),
			("bad device token", ["BadDeviceToken", "TimeoutError"], False, True),
			("transient error", ["PayloadTooLarge", "CommunicationError"], True, True),
		]

		for name, descriptions, token2_active, token3_active in scenarios:
			with self.subTest(name):
				APNSDevice.objects.update(active=True)
				self._bulk_send(mock_apns, [("200", None)] + [("400", d) for d in descriptions])

				self.assertEqual(
					dict(APNSDevice.objects.values_list("registration_id", "active")),
					{
						"token1": True,
						"token2": token2_active,
						"token3": token3_active,
					},
				)
