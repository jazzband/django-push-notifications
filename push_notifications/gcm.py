"""
Firebase Cloud Messaging
Previously known as GCM / C2DM
Documentation is available on the Firebase Developer website:
https://firebase.google.com/docs/cloud-messaging/
"""

from copy import copy
from typing import List, Union

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError, InvalidArgumentError

from .conf import get_manager


# Valid keys for FCM messages. Reference:
# https://firebase.google.com/docs/cloud-messaging/http-server-ref
FCM_NOTIFICATIONS_PAYLOAD_KEYS = [
	"title", "body", "icon", "image", "sound", "badge", "color", "tag", "click_action",
	"body_loc_key", "body_loc_args", "title_loc_key", "title_loc_args", "android_channel_id"
]


def dict_to_fcm_message(data: dict, dry_run=False, **kwargs) -> messaging.Message:
	"""
	Constructs a messaging.Message from the old dictionary.

	FCM_NOTIFICATION_PAYLOAD_KEYS are being put into the AndroidNotification
	FCM_OPTIONS_KEYS are being put into the AndroidConfig
	FCM_TARGETS_KEYS is mapped to either topic, token or condition

	If dry_run is included and its value is True, no message will be returned, so nothing is accidentally sent.
	"""

	data = data.copy()

	# in the old version, dry run was being passed in the data dict
	# now it needs to be passed as an argument for the send_each method
	# to not accidentally sending messages, do not return a message here.
	if "dry_run" in data and data.pop("dry_run", False) or dry_run:
		return None

	android_notification = None

	notification_payload = {}
	if "message" in data:
		notification_payload["body"] = data.pop("message", None)
	for key in FCM_NOTIFICATIONS_PAYLOAD_KEYS:
		value_from_extra = data.pop(key, None)
		if value_from_extra:
			notification_payload[key] = value_from_extra
		value_from_kwargs = kwargs.pop(key, None)
		if value_from_kwargs:
			notification_payload[key] = value_from_kwargs
	if notification_payload:
		# channel id is the one that is different
		notification_payload["channel_id"] = notification_payload.pop("android_channel_id", None)
		notification_payload["notification_count"] = notification_payload.pop("badge", None)
		android_notification = messaging.AndroidNotification(**notification_payload)

	android_config = messaging.AndroidConfig(
		collapse_key=data.pop("collapse_key", None) or kwargs.get("collapse_key", None),
		priority=data.pop("priority", None) or kwargs.get("priority", None),
		ttl=data.pop("time_to_live", None) or kwargs.get("time_to_live", None),
		restricted_package_name=data.pop("restricted_package_name", None) or kwargs.get(
			"restricted_package_name", None),
		data=data,
		notification=android_notification
	)

	message = messaging.Message(data=data, android=android_config)

	# set correct receiver
	to: str = data.pop("to", None) or kwargs.get("to", None)
	condition = data.pop("condition", None) or kwargs.get("condition", None)
	notification_key = data.pop(
		"notification_key", None) or kwargs.get("notification_key", None)

	# topic is set with /topic/ prefix, message can handle this format as well
	if to and to.startswith("/topic/"):
		message.topic = to
	else:
		message.token = notification_key or to
	message.condition = condition

	return message


def _chunks(l, n):
	"""
	Yield successive chunks from list \a l with a maximum size \a n
	"""
	for i in range(0, len(l), n):
		yield l[i:i + n]


# Error codes: https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode
fcm_error_list = [
	messaging.UnregisteredError,
	messaging.SenderIdMismatchError,
	InvalidArgumentError,
]

fcm_error_list_str = [x.code for x in fcm_error_list]


def _validate_exception_for_deactivation(exc: Union[FirebaseError]) -> bool:
	if not exc:
		return False
	exc_type = type(exc)
	if exc_type == str:
		return exc in fcm_error_list_str
	return (
		exc_type == InvalidArgumentError and exc.cause == "Invalid registration"
	) or (exc_type in fcm_error_list)


def _deactivate_devices_with_error_results(
	registration_ids: List[str],
	results: List[Union[messaging.SendResponse, messaging.ErrorInfo]],
) -> List[str]:
	if not results:
		return []
	if isinstance(results[0], messaging.SendResponse):
		deactivated_ids = [
			token
			for item, token in zip(results, registration_ids)
			if _validate_exception_for_deactivation(item.exception)
		]
	else:
		deactivated_ids = [
			registration_ids[x.index]
			for x in results
			if _validate_exception_for_deactivation(x.reason)
		]
	from .models import GCMDevice
	GCMDevice.objects.filter(registration_id__in=deactivated_ids).update(active=False)
	return deactivated_ids


def _prepare_message(message: messaging.Message, token: str):
	message.token = token
	return copy(message)


def send_message(
	registration_ids,
	message: messaging.Message,
	application_id=None,
	dry_run=False,
	**kwargs
):
	"""
	Sends an FCM notification to one or more registration_ids. The registration_ids
	can be a list or a single string.

	:param registration_ids: A list of registration ids or a single string
	:param message: The Message object, use `dict_to_fcm_message` to convert dict to Message
	:param application_id: The application id to use.
	:param dry_run: If True, no message will be sent.

	:return: A BatchResponse object
	"""
	max_recipients = get_manager().get_max_recipients(application_id)
	app = get_manager().get_firebase_app(application_id) if application_id else None

	# Checks for valid recipient
	if registration_ids is None and message.topic is None and message.condition is None:
		return

	# Bundles the registration_ids in an list if only one is sent
	if not isinstance(registration_ids, list):
		registration_ids = [registration_ids] if registration_ids else None

	# FCM only allows up to 1000 reg ids per bulk message
	# https://firebase.google.com/docs/cloud-messaging/server#http-request
	if registration_ids:
		ret: List[messaging.SendResponse] = []
		for chunk in _chunks(registration_ids, max_recipients):
			messages = [
				_prepare_message(message, token) for token in chunk
			]
			responses = messaging.send_each(messages, dry_run=dry_run, app=app).responses
			ret.extend(responses)
		_deactivate_devices_with_error_results(registration_ids, ret)
		return messaging.BatchResponse(ret)
	else:
		return messaging.BatchResponse([])


send_bulk_message = send_message
