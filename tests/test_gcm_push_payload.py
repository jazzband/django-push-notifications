from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from firebase_admin.messaging import Message

from push_notifications.gcm import dict_to_fcm_message, send_message

from .responses import FCM_SUCCESS


class GCMPushPayloadTest(TestCase):

	def test_fcm_push_payload(self):
		with mock.patch("firebase_admin.messaging.send_each", return_value=FCM_SUCCESS) as p:
			message = dict_to_fcm_message({"message": "Hello world"})

			send_message("abc", message)

			self.assertEqual(p.call_count, 1)

			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# only one message
			messages = call[0][0]
			self.assertEqual(len(messages), 1)

			message = messages[0]
			self.assertIsInstance(message, Message)
			self.assertEqual(message.token, "abc")
			self.assertEqual(message.android.notification.body, "Hello world")

	def test_fcm_push_payload_many(self):
		with mock.patch("firebase_admin.messaging.send_each", return_value=FCM_SUCCESS) as p:
			message = dict_to_fcm_message({"message": "Hello world"})

			send_message(["abc", "123"], message)

			# one call
			self.assertEqual(p.call_count, 1)
			call = p.call_args
			kwargs = call[1]

			self.assertTrue("dry_run" in kwargs)
			self.assertFalse(kwargs["dry_run"])
			self.assertTrue("app" in kwargs)
			self.assertIsNone(kwargs["app"])

			# two message
			messages = call[0][0]
			self.assertEqual(len(messages), 2)

			message_one = messages[0]
			self.assertIsInstance(message_one, Message)
			self.assertEqual(message_one.token, "abc")
			self.assertEqual(message_one.android.notification.body, "Hello world")

			message_two = messages[1]
			self.assertIsInstance(message_two, Message)
			self.assertEqual( message_two.token,"123")
			self.assertEqual( message_two.android.notification.body, "Hello world")

	def test_push_payload_with_app_id(self):
		with self.assertRaises(ImproperlyConfigured) as ic:
			send_message("abc", {"message": "Hello world"}, application_id="test")

		self.assertEqual(
			str(ic.exception),
			("LegacySettings does not support application_id. To enable "
			 "multiple application support, use push_notifications.conf.AppSettings.")
		)
