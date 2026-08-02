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
			restricted_package_name="restricted.package.name",
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

		assert isinstance(message, Message)
		assert message.android.collapse_key == "Collapse Key"
		assert message.android.priority == "High"
		assert message.android.ttl == 3600
		assert message.android.restricted_package_name == "restricted.package.name"
		assert getattr(message, "priority", None) is None

	def test_nested_message_payload(self):
		payload = {
			"message": {
				"topic": "subscriber-updates",
				"notification": {
					"body": "This week's edition is now available.",
					"title": "NewsMagazine.com",
				},
				"data": {
					"volume": "3.21.15",
					"contents": "http://www.news-magazine.com/world-week/21659772",
				},
				"android": {
					"priority": "normal",
				},
				"apns": {
					"headers": {
						"apns-priority": "5",
					},
				},
				"webpush": {
					"headers": {
						"Urgency": "high",
					},
				},
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic == "subscriber-updates"
		assert message.token is None
		assert message.condition is None
		assert message.notification is not None
		assert message.notification.title == "NewsMagazine.com"
		assert message.notification.body == "This week's edition is now available."
		assert message.data == {
			"volume": "3.21.15",
			"contents": "http://www.news-magazine.com/world-week/21659772",
		}
		assert message.android is not None
		assert message.android.priority == "normal"
		assert getattr(message, "priority", None) is None
		assert message.android.data is None or message.android.data == {}
		assert message.android.notification is None
		assert message.apns is not None
		assert message.apns.headers == {"apns-priority": "5"}
		assert message.webpush is not None
		assert message.webpush.headers == {"Urgency": "high"}

	def test_nested_message_without_android(self):
		payload = {
			"message": {
				"notification": {"title": "Hello", "body": "World"},
				"data": {"key": "value"},
				"topic": "subscriber-updates",
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.android is None
		assert message.apns is None
		assert message.webpush is None
		assert message.notification.title == "Hello"
		assert message.notification.body == "World"
		assert message.data == {"key": "value"}
		assert message.topic == "subscriber-updates"

	def test_nested_message_without_apns(self):
		payload = {
			"message": {
				"notification": {"title": "Hello", "body": "World"},
				"android": {"priority": "high"},
				"webpush": {"headers": {"Urgency": "high"}},
				"data": {"key": "value"},
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.android is not None
		assert message.android.priority == "high"
		assert message.apns is None
		assert message.webpush is not None
		assert message.webpush.headers == {"Urgency": "high"}
		assert message.notification.title == "Hello"
		assert message.notification.body == "World"
		assert message.data == {"key": "value"}

	def test_nested_message_without_webpush(self):
		payload = {
			"message": {
				"notification": {"title": "Hello", "body": "World"},
				"android": {"priority": "normal"},
				"apns": {"headers": {"apns-priority": "5"}},
				"data": {"key": "value"},
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.android is not None
		assert message.android.priority == "normal"
		assert message.apns is not None
		assert message.apns.headers == {"apns-priority": "5"}
		assert message.webpush is None
		assert message.notification.title == "Hello"
		assert message.notification.body == "World"
		assert message.data == {"key": "value"}

	def test_nested_message_without_notification(self):
		payload = {
			"message": {
				"android": {"priority": "high"},
				"apns": {"headers": {"apns-priority": "5"}},
				"webpush": {"headers": {"Urgency": "high"}},
				"data": {"key": "value"},
				"topic": "subscriber-updates",
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.android is not None
		assert message.android.priority == "high"
		assert message.apns is not None
		assert message.apns.headers == {"apns-priority": "5"}
		assert message.webpush is not None
		assert message.webpush.headers == {"Urgency": "high"}
		assert message.notification is None
		assert message.data == {"key": "value"}
		assert message.topic == "subscriber-updates"

	def test_nested_message_topic(self):
		payload = {"message": {"topic": "subscriber-updates"}}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic == "subscriber-updates"
		assert message.token is None
		assert message.condition is None

	def test_nested_message_token(self):
		payload = {
			"message": {
				"token": "token-123",
				"notification": {
					"title": "Hello",
					"body": "World",
				},
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic is None
		assert message.token == "token-123"
		assert message.condition is None
		assert message.notification.title == "Hello"
		assert message.notification.body == "World"

	def test_nested_message_condition(self):
		payload = {
			"message": {
				"condition": "'news' in topics",
				"notification": {
					"title": "Hello",
					"body": "World",
				},
			},
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic is None
		assert message.token is None
		assert message.condition == "'news' in topics"
		assert message.notification.title == "Hello"
		assert message.notification.body == "World"

	def test_nested_message_data(self):
		payload = {"message": {"data": {"key": "value"}}}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.data == {"key": "value"}
		assert message.android is None
		assert message.apns is None
		assert message.webpush is None

	def test_nested_message_notification(self):
		payload = {"message": {"notification": {"title": "Hello", "body": "World"}}}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.notification is not None
		assert message.notification.title == "Hello"
		assert message.notification.body == "World"

	def test_legacy_flat_payload_compatibility(self):
		payload = {
			"message": "Hello World",
			"to": "/topic/legacy",
			"title": "Legacy Title",
			"body": "Legacy Body",
			"priority": "high",
			"time_to_live": 3600,
		}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic == "/topic/legacy"
		assert message.token is None
		assert message.condition is None
		assert message.android.priority == "high"
		assert message.android.ttl == 3600
		assert message.android.notification.title == "Legacy Title"
		assert message.android.notification.body == "Legacy Body"

	def test_legacy_flat_payload_string_message(self):
		payload = {"message": "Hello World"}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.android is not None
		assert message.android.notification.body == "Hello World"

	def test_legacy_flat_payload_topic(self):
		payload = {"message": "Hello World", "to": "/topic/legacy"}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic == "/topic/legacy"
		assert message.token is None
		assert message.condition is None

	def test_legacy_flat_payload_token(self):
		payload = {"message": "Hello World", "to": "token-123"}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic is None
		assert message.token == "token-123"
		assert message.condition is None

	def test_legacy_flat_payload_condition(self):
		payload = {"message": "Hello World", "condition": "'news' in topics"}

		message = dict_to_fcm_message(payload)

		assert isinstance(message, Message)
		assert message.topic is None
		assert message.token is None
		assert message.condition == "'news' in topics"

	def test_receiver_mapping_topic(self):
		payload = {
			"message": "Hello World",
			"to": "/topic/...",
		}

		message = dict_to_fcm_message(payload)
		assert isinstance(message, Message)
		assert message.topic == "/topic/..."
		assert message.token is None

	def test_receiver_mapping_token(self):
		payload = {
			"message": "Hello World",
			"to": "...",
		}

		message = dict_to_fcm_message(payload)
		assert isinstance(message, Message)
		assert message.topic is None
		assert message.token == "..."

	def test_receiver_mapping_condition(self):
		payload = {
			"message": "Hello World",
			"condition": "...",
		}

		message = dict_to_fcm_message(payload)
		assert isinstance(message, Message)
		assert message.condition == "..."
