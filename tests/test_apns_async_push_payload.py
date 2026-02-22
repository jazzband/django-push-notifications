import sys
import time
from unittest import mock

import pytest
from django.test import TestCase


try:
	from aioapns.common import NotificationResult
	from push_notifications.apns_async import TokenCredentials, apns_send_message, apns_send_bulk_message, CertificateCredentials, BulkNotificationResult
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
		result =  NotificationResult(
			"123", "400"
		)
		mock_cert_pool.return_value.send_notification.return_value = result
		err_func = mock.AsyncMock()
		with pytest.raises(Exception):
			apns_send_message(
				"123",
				"sample",
				creds=CertificateCredentials(
					client_cert="dummy/path.pem",
				),
				topic="default",
				err_func=err_func,
			)
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



class APNSAsyncErrorHandlingTests(TestCase):

    @mock.patch("push_notifications.apns_async.asyncio.run")
    @mock.patch("push_notifications.apns_async.get_manager")
    def test_returns_bulk_notification_result(self, mock_manager, mock_asyncio_run):
        mock_manager.return_value.get_apns_topic.return_value = "com.example.app"

        mock_asyncio_run.return_value = [
            ("token1", NotificationResult("123", "200")),
        ]

        result = apns_send_bulk_message(
            registration_ids=["token1"],
            alert="Test",
            creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
        )

        self.assertIsInstance(result, BulkNotificationResult)
        self.assertIsInstance(result.results, dict)
        self.assertIsInstance(result.errors, list)

    @mock.patch("push_notifications.apns_async.asyncio.run")
    @mock.patch("push_notifications.apns_async.get_manager")
    def test_all_success_returns_empty_errors(self, mock_manager, mock_asyncio_run):
        # successful notifications return empty errors list

        mock_manager.return_value.get_apns_topic.return_value = "com.example.app"

        mock_asyncio_run.return_value = [
            ("token1", NotificationResult("123", "200")),
            ("token2", NotificationResult("124", "200")),
        ]

        result = apns_send_bulk_message(
            registration_ids=["token1", "token2"],
            alert="Test",
            creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
        )

        self.assertEqual(len(result.errors), 0)
        self.assertFalse(result.has_errors)
        self.assertEqual(result.results["token1"], "Success")
        self.assertEqual(result.results["token2"], "Success")

    @mock.patch("push_notifications.apns_async.asyncio.run")
    @mock.patch("push_notifications.apns_async.get_manager")
    def test_partial_failure_returns_error_objects(self, mock_manager, mock_asyncio_run):
        mock_manager.return_value.get_apns_topic.return_value = "com.example.app"

        mock_asyncio_run.return_value = [
            ("token1", NotificationResult("123", "200")),
            ("token2", NotificationResult("124", "400", description="BadDeviceToken")),
        ]

        result = apns_send_bulk_message(
            registration_ids=["token1", "token2"],
            alert="Test",
            creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
        )

        self.assertEqual(result.results["token1"], "Success")
        self.assertEqual(result.results["token2"], "BadDeviceToken")

        self.assertEqual(len(result.errors), 1)
        self.assertTrue(result.has_errors)

        error = result.errors[0]
        self.assertEqual(error["registration_id"], "token2")
        self.assertEqual(error["error_type"], "BadDeviceToken")
        self.assertEqual(error["error_message"], "BadDeviceToken")
        self.assertIn("timestamp", error)

    @mock.patch("push_notifications.apns_async.asyncio.run")
    @mock.patch("push_notifications.apns_async.get_manager")
    def test_multiple_errors_all_captured(self, mock_manager, mock_asyncio_run):
        mock_manager.return_value.get_apns_topic.return_value = "com.example.app"

        mock_asyncio_run.return_value = [
            ("token1", NotificationResult("123", "400", description="Unregistered")),
            ("token2", NotificationResult("124", "400", description="BadDeviceToken")),
            ("token3", NotificationResult("125", "400", description="TimeoutError")),
        ]

        result = apns_send_bulk_message(
            registration_ids=["token1", "token2", "token3"],
            alert="Test",
            creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
        )

        self.assertEqual(len(result.errors), 3)
        self.assertTrue(result.has_errors)

        error_types = [e["error_type"] for e in result.errors]
        self.assertIn("Unregistered", error_types)
        self.assertIn("BadDeviceToken", error_types)
        self.assertIn("TimeoutError", error_types)

    @mock.patch("push_notifications.apns_async.models.APNSDevice.objects.filter")
    @mock.patch("push_notifications.apns_async.asyncio.run")
    @mock.patch("push_notifications.apns_async.get_manager")
    def test_unregistered_tokens_marked_inactive(self, mock_manager, mock_asyncio_run, mock_filter):
        mock_manager.return_value.get_apns_topic.return_value = "com.example.app"
        mock_update = mock.Mock()
        mock_filter.return_value.update = mock_update

        mock_asyncio_run.return_value = [
            ("token1", NotificationResult("123", "200")),
            ("token2", NotificationResult("124", "400", description="Unregistered")),
            ("token3", NotificationResult("125", "400", description="BadDeviceToken")),
        ]

        _ = apns_send_bulk_message(
            registration_ids=["token1", "token2", "token3"],
            alert="Test",
            creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
        )

        mock_filter.assert_called_once()
        call_args = mock_filter.call_args[1]
        self.assertIn("token2", call_args["registration_id__in"])
        self.assertIn("token3", call_args["registration_id__in"])
        mock_update.assert_called_once_with(active=False)

    @mock.patch("push_notifications.apns_async.asyncio.run")
    @mock.patch("push_notifications.apns_async.get_manager")
    def test_does_not_raise_exception_on_errors(self, mock_manager, mock_asyncio_run):
        # Test that errors don't raise exceptions - they're returned in the result
        mock_manager.return_value.get_apns_topic.return_value = "com.example.app"

        mock_asyncio_run.return_value = [
            ("token1", NotificationResult("123", "400", description="Unregistered")),
        ]

        try:
            result = apns_send_bulk_message(
                registration_ids=["token1"],
                alert="Test",
                creds=TokenCredentials(key="aaa", key_id="bbb", team_id="ccc"),
            )
            exception_raised = False
        except Exception:
            exception_raised = True

        self.assertFalse(exception_raised, "apns_send_bulk_message should not raise exceptions on errors")
        self.assertTrue(result.has_errors)
