import sys
import time
from unittest import mock

import pytest
from django.conf import settings
from django.test import TestCase, override_settings

from push_notifications.models import APNSDevice


try:
	from aioapns.common import NotificationResult
	from push_notifications.apns_async import (
		apns_send_bulk_message, apns_send_message, BulkNotificationResult,
		CertificateCredentials, DeliveryError, SUCCESS, TokenCredentials,
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

	@override_settings()
	@mock.patch("push_notifications.apns_async.asyncio.wait_for")
	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_send_uses_configured_timeout(self, mock_apns, mock_wait_for):
		async def await_result(awaitable, timeout=None):
			return await awaitable

		mock_wait_for.side_effect = await_result

		registration_id = (
			"3a1f7c9e2b4d6f8a0c2e4b6d8f0a1c3e"
			"5b7d9f1a3c5e7b9d1f3a5c7e9b1d3f5a"
		)
		creds = TokenCredentials(key="aaa", key_id="bbb", team_id="ccc")

		# with default value of 5 seconds
		apns_send_message(registration_id, "Hello world", creds=creds)
		self.assertEqual(mock_wait_for.call_args.kwargs["timeout"], 5)

		# configured to 10 seconds
		settings.PUSH_NOTIFICATIONS_SETTINGS.update({"APNS_ERROR_TIMEOUT": 10})

		apns_send_message(registration_id, "Hello world", creds=creds)
		self.assertEqual(mock_wait_for.call_args.kwargs["timeout"], 10)


class APNSAsyncBulkMessageErrorHandlingTest(TestCase):
	REGISTRATION_IDS = [
		"1e5a9c3f7b0d24e8a1c5f9b3d6a0e4c8f1b5d9a2c6e0f4b8d3a7c1e5f9b0d4a2c",
		"4b8e2f6a1c3d59a7b0d4e2f8c1a5b3d6f9e0c2a5b8d1f4e7c0a3b6d9f2e5c8a1",
		"c4a7e0b3f6d91a5c8e2b7f4d0a3c6e9f2b5d8a1c4e7f0b3d6a9c2e5f8b1d4a7c",
	]

	def setUp(self):
		for registration_id in self.REGISTRATION_IDS:
			APNSDevice.objects.create(registration_id=registration_id)

	def _bulk_send(self, mock_apns, descriptions):
		registration_ids = list(
			APNSDevice.objects.order_by("registration_id").values_list(
				"registration_id", flat=True
			)
		)
		mock_apns.return_value.send_notification.side_effect = [
			NotificationResult(
				notification_id="8f14e45f-ceea-467a-9d0c-1e2b3c4d5e6f",
				status="200" if description is None else "400",
				description=description,
			)
			for description in descriptions
		]
		return apns_send_bulk_message(
			registration_ids=registration_ids,
			alert="Happy Customer Service Week!",
			creds=TokenCredentials(
				key="aaa", key_id="ABCDE12345", team_id="FGHIJ67890"
			),
		)

	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_reports_errors_and_deactivates_rejected_registration_ids(self, mock_apns):
		# per token: the description APNS returned, or None when APNS accepted it.
		# then the expected results, the expected errors as (position, type)
		# pairs, and the expected ``APNSDevice.active`` flags.
		scenarios = [
			(
				"every notification delivered",
				[None, None, None],
				[SUCCESS, SUCCESS, SUCCESS],
				[],
				[True, True, True],
			),
			(
				"one unregistered device",
				[None, "Unregistered", None],
				[SUCCESS, "Unregistered", SUCCESS],
				[(1, "Unregistered")],
				[True, False, True],
			),
			(
				"two permanent failures",
				["BadDeviceToken", None, "DeviceTokenNotForTopic"],
				["BadDeviceToken", SUCCESS, "DeviceTokenNotForTopic"],
				[(0, "BadDeviceToken"), (2, "DeviceTokenNotForTopic")],
				[False, True, False],
			),
			(
				"a timeout keeps the device",
				["TimeoutError", None, None],
				["TimeoutError", SUCCESS, SUCCESS],
				[(0, "TimeoutError")],
				[True, True, True],
			),
			(
				"payload and connection failures keep the device",
				[None, "PayloadTooLarge", "CommunicationError: connection reset by peer"],
				[
					SUCCESS,
					"PayloadTooLarge",
					"CommunicationError: connection reset by peer",
				],
				[
					(1, "PayloadTooLarge"),
					(2, "CommunicationError: connection reset by peer"),
				],
				[True, True, True],
			),
		]

		for name, descriptions, expected_results, expected_errors, expected_active in scenarios:
			with self.subTest(name):
				APNSDevice.objects.update(active=True)
				result = self._bulk_send(mock_apns, descriptions)

				self.assertIsInstance(result, BulkNotificationResult)
				self.assertEqual(result.registration_ids, self.REGISTRATION_IDS)
				self.assertEqual(
					result.results, dict(zip(self.REGISTRATION_IDS, expected_results))
				)
				self.assertIsNone(result.result_for("a-token-that-was-never-sent"))
				self.assertEqual(result.has_errors, bool(expected_errors))
				self.assertEqual(
					result.errors,
					[
						DeliveryError(
							registration_id=self.REGISTRATION_IDS[position],
							error_type=error_type,
							error_message=error_type,
							timestamp=mock.ANY,
						)
						for position, error_type in expected_errors
					],
				)
				self.assertEqual(
					list(
						APNSDevice.objects.order_by("registration_id").values_list(
							"registration_id", "active"
						)
					),
					list(zip(self.REGISTRATION_IDS, expected_active)),
				)

	@override_settings()
	@mock.patch("push_notifications.apns_async.APNs", autospec=True)
	def test_queryset_send_message_returns_legacy_results(self, mock_apns):
		settings.PUSH_NOTIFICATIONS_SETTINGS.update(
			{"APNS_CERTIFICATE": "/path/to/apns/certificate.pem"}
		)

		mock_apns.return_value.send_notification.side_effect = [
			NotificationResult(
				notification_id="8f14e45f-ceea-467a-9d0c-1e2b3c4d5e6f", status="200"
			),
			NotificationResult(
				notification_id="c9f0f895-fb98-4b9e-b1a1-e6f8c1d2a3b4",
				status="400",
				description="Unregistered",
			),
			NotificationResult(
				notification_id="45c48cce-2e2d-4fbd-bb1f-b3d3f4e5f6a7",
				status="200",
			),
		]

		results = APNSDevice.objects.all().send_message("Your order has shipped")

		self.assertEqual(
			results,
			[
				{
					self.REGISTRATION_IDS[0]: SUCCESS,
					self.REGISTRATION_IDS[1]: "Unregistered",
					self.REGISTRATION_IDS[2]: SUCCESS,
				}
			],
		)
