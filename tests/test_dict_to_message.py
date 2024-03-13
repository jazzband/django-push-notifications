from django.test import TestCase
from firebase_admin.messaging import Message

from push_notifications.gcm import dict_to_fcm_message


class DictToMessageTest(TestCase):

	def test_dry_run_none(self):
		message_no = dict_to_fcm_message({"message": "Hello World", "dry_run": True})
		message_no_kwargs = dict_to_fcm_message({"message": "Hello World"}, dry_run=True)
		message_yes = dict_to_fcm_message({"message": "Hello World", "dry_run": False})

		assert message_no is None
		assert message_no_kwargs is None
		assert isinstance(message_yes, Message)
		assert message_yes.android.notification.body == "Hello World"

	def test_kwargs(self):
		message = dict_to_fcm_message(
			{},
			time_to_live=3600,
			collapse_key="collapse key",
			priority="high",
			restricted_package_name="restricted.package.name"
		)

		assert message.android.ttl == 3600
		assert message.android.collapse_key == "collapse key"
		assert message.android.priority == "high"
		assert message.android.restricted_package_name == "restricted.package.name"

	def test_payload_keys(self):
		"""
		old FCM_NOTIFICATIONS_PAYLOAD_KEYS payload is mapped to message object correctly
		"""
		payload = {
			"message": "Hello World",
			"title": "Title",
			"body": "Body",
			"icon": "Icon",
			"image": "Image",
			"sound": "Sound",
			"badge": "10",
			"color": "Color",
			"tag": "Tag",
			"click_action": "Click Action",
			"body_loc_key": "Body Loc Key",
			"body_loc_args": "Body Loc Args",
			"title_loc_key": "Title Loc Key",
			"title_loc_args": "Title Loc Args",
			"android_channel_id": "Android Channel Id",
		}

		message = dict_to_fcm_message(payload)

		assert message.android.notification.title == "Title"
		assert message.android.notification.body == "Body"
		assert message.android.notification.icon == "Icon"
		assert message.android.notification.image == "Image"
		assert message.android.notification.sound == "Sound"
		assert message.android.notification.notification_count == "10"
		assert message.android.notification.color == "Color"
		assert message.android.notification.tag == "Tag"
		assert message.android.notification.click_action == "Click Action"
		assert message.android.notification.body_loc_key == "Body Loc Key"
		assert message.android.notification.body_loc_args == "Body Loc Args"
		assert message.android.notification.title_loc_key == "Title Loc Key"
		assert message.android.notification.title_loc_args == "Title Loc Args"
		assert message.android.notification.channel_id == "Android Channel Id"

	def test_fcm_options(self):
		"""
		old FCM_OPTIONS_KEYS payload is mapped to message object correctly
		"""

		payload = {
			"message": "Hello World",
			"collapse_key": "Collapse Key",
			"priority": "High",
			"time_to_live": 3600,
			"restricted_package_name": "restricted.package.name",
		}

		message = dict_to_fcm_message(payload)

		assert message.android.collapse_key == "Collapse Key"
		assert message.android.priority == "High"
		assert message.android.ttl == 3600
		assert message.android.restricted_package_name == "restricted.package.name"

	def test_receiver_mapping_topic(self):
		payload = {
			"message": "Hello World",
			"to": "/topic/...",
		}

		message = dict_to_fcm_message(payload)
		assert message.topic == "/topic/..."
		assert message.token is None

	def test_receiver_mapping_token(self):
		payload = {
			"message": "Hello World",
			"to": "...",
		}

		message = dict_to_fcm_message(payload)
		assert message.topic is None
		assert message.token == "..."

	def test_receiver_mapping_condition(self):
		payload = {
			"message": "Hello World",
			"condition": "...",
		}

		message = dict_to_fcm_message(payload)
		assert message.condition == "..."
