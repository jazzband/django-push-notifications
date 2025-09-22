import asyncio
import time

from dataclasses import asdict, dataclass
from typing import Awaitable, Callable, Dict, Optional, Union

from aioapns import APNs, ConnectionError, NotificationRequest
from aioapns.common import NotificationResult

from . import models
from .conf import get_manager
from .exceptions import APNSServerError, APNSError

ErrFunc = Optional[Callable[[NotificationRequest, NotificationResult], Awaitable[None]]]
"""function to proces errors from aioapns send_message"""


class NotSet:
	def __init__(self):
		raise RuntimeError("NotSet cannot be instantiated")


class Credentials:
	pass


@dataclass
class TokenCredentials(Credentials):
	key: str
	key_id: str
	team_id: str


@dataclass
class CertificateCredentials(Credentials):
	client_cert: str


@dataclass
class Alert:
	"""
	The information for displaying an alert. A dictionary is recommended. If you specify a string, the alert displays your string as the body text.

	https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/generating_a_remote_notification
	"""

	title: str = NotSet
	"""
	The title of the notification. Apple Watch displays this string in the short look notification interface. Specify a string that’s quickly understood by the user.
	"""

	subtitle: str = NotSet
	"""
	Additional information that explains the purpose of the notification.
	"""

	body: str = NotSet
	"""
	The content of the alert message.
	"""

	launch_image: str = NotSet
	"""
	The name of the launch image file to display. If the user chooses to launch your app, the contents of the specified image or storyboard file are displayed instead of your app’s normal launch image.
	"""

	title_loc_key: str = NotSet
	"""
	The key for a localized title string. Specify this key instead of the title key to retrieve the title from your app’s Localizable.strings files. The value must contain the name of a key in your strings file
	"""

	title_loc_args: list[str] = NotSet
	"""
	An array of strings containing replacement values for variables in your title string. Each %@ character in the string specified by the title-loc-key is replaced by a value from this array. The first item in the array replaces the first instance of the %@ character in the string, the second item replaces the second instance, and so on.
	"""

	subtitle_loc_key: str = NotSet
	"""
	The key for a localized subtitle string. Use this key, instead of the subtitle key, to retrieve the subtitle from your app’s Localizable.strings file. The value must contain the name of a key in your strings file.
	"""

	subtitle_loc_args: list[str] = NotSet
	"""
	An array of strings containing replacement values for variables in your title string. Each %@ character in the string specified by subtitle-loc-key is replaced by a value from this array. The first item in the array replaces the first instance of the %@ character in the string, the second item replaces the second instance, and so on.
	"""

	loc_key: str = NotSet
	"""
	The key for a localized message string. Use this key, instead of the body key, to retrieve the message text from your app’s Localizable.strings file. The value must contain the name of a key in your strings file.
	"""

	loc_args: list[str] = NotSet
	"""
	An array of strings containing replacement values for variables in your message text. Each %@ character in the string specified by loc-key is replaced by a value from this array. The first item in the array replaces the first instance of the %@ character in the string, the second item replaces the second instance, and so on.
	"""

	sound: Union[str, any] = NotSet
	"""
	string
	The name of a sound file in your app’s main bundle or in the Library/Sounds folder of your app’s container directory. Specify the string “default” to play the system sound. Use this key for regular notifications. For critical alerts, use the sound dictionary instead. For information about how to prepare sounds, see UNNotificationSound.

	dictionary
	A dictionary that contains sound information for critical alerts. For regular notifications, use the sound string instead.
	"""

	def asDict(self) -> dict[str, any]:
		python_dict = asdict(self)
		return {
			key.replace("_", "-"): value
			for key, value in python_dict.items()
			if value is not NotSet
		}


def _create_notification_request_from_args(
	registration_id: str,
	alert: Union[str, Alert],
	badge: int = None,
	sound: str = None,
	extra: dict = {},
	expiration: int = None,
	thread_id: str = None,
	loc_key: str = None,
	priority: int = None,
	collapse_id: str = None,
	aps_kwargs: dict = {},
	message_kwargs: dict = {},
	notification_request_kwargs: dict = {},
):
	if alert is None:
		alert = Alert(body="")

	if loc_key:
		if isinstance(alert, str):
			alert = Alert(body=alert)
		alert.loc_key = loc_key

	if isinstance(alert, Alert):
		alert = alert.asDict()

	notification_request_kwargs_out = notification_request_kwargs.copy()

	if expiration is not None:
		notification_request_kwargs_out["time_to_live"] = expiration - int(time.time())
	if priority is not None:
		notification_request_kwargs_out["priority"] = priority

	if collapse_id is not None:
		notification_request_kwargs_out["collapse_key"] = collapse_id

	request = NotificationRequest(
		device_token=registration_id,
		message={
			"aps": {
				"alert": alert,
				"badge": badge,
				"sound": sound,
				"thread-id": thread_id,
				**aps_kwargs,
			},
			**extra,
			**message_kwargs,
		},
		**notification_request_kwargs_out,
	)

	return request


def _create_client(
	creds: Credentials = None,
	application_id: str = None,
	topic=None,
	err_func: ErrFunc = None,
) -> APNs:
	use_sandbox = get_manager().get_apns_use_sandbox(application_id)
	if topic is None:
		topic = get_manager().get_apns_topic(application_id)
	if creds is None:
		creds = _get_credentials(application_id)

	client = APNs(
		**asdict(creds),
		topic=topic,  # Bundle ID
		use_sandbox=use_sandbox,
		err_func=err_func,
	)
	return client


def _get_credentials(application_id):
	if not get_manager().has_auth_token_creds(application_id):
		# TLS certificate authentication
		cert = get_manager().get_apns_certificate(application_id)
		return CertificateCredentials(
			client_cert=cert,
		)
	else:
		# Token authentication
		keyPath, keyId, teamId = get_manager().get_apns_auth_creds(application_id)
		# No use getting a lifetime because this credential is
		# ephemeral, but if you're looking at this to see how to
		# create a credential, you could also pass the lifetime and
		# algorithm. Neither of those settings are exposed in the
		# settings API at the moment.
		return TokenCredentials(key=keyPath, key_id=keyId, team_id=teamId)


def apns_send_message(
	registration_id: str,
	alert: Union[str, Alert],
	application_id: str = None,
	creds: Credentials = None,
	topic: str = None,
	badge: int = None,
	sound: str = None,
	content_available: bool = None,
	extra: dict = {},
	expiration: int = None,
	thread_id: str = None,
	loc_key: str = None,
	priority: int = None,
	collapse_id: str = None,
	mutable_content: bool = False,
	category: str = None,
	err_func: ErrFunc = None,
):
	"""
	Sends an APNS notification to a single registration_id.
	If sending multiple notifications, it is more efficient to use
	apns_send_bulk_message()

	Note that if set alert should always be a string. If it is not set,
	it won"t be included in the notification. You will need to pass None
	to this for silent notifications.


	:param registration_id: The registration_id of the device to send to
	:param alert: The alert message to send
	:param application_id: The application_id to use
	:param creds: The credentials to use
	:param mutable_content: If True, the "mutable-content" flag will be set to 1.
	                    This allows the app's Notification Service Extension to modify
	                    the notification before it is displayed.
	:param category: The category identifier for actionable notifications.
	                 This should match a category identifier defined in the app's
	                 Notification Content Extension or UNNotificationCategory configuration.
	                 It allows the app to display custom actions with the notification.
	:param content_available: If True the `content-available` flag will be set to 1, allowing the app to be woken up in the background
	"""
	results = apns_send_bulk_message(
		registration_ids=[registration_id],
		alert=alert,
		application_id=application_id,
		creds=creds,
		topic=topic,
		badge=badge,
		sound=sound,
		content_available=content_available,
		extra=extra,
		expiration=expiration,
		thread_id=thread_id,
		loc_key=loc_key,
		priority=priority,
		collapse_id=collapse_id,
		mutable_content=mutable_content,
		category=category,
		err_func=err_func,
	)

	for result in results.values():
		if result == "Success":
			return {"results": [result]}
		else:
			return {"results": [{"error": result}]}


def apns_send_bulk_message(
	registration_ids: list[str],
	alert: Union[str, Alert],
	application_id: str = None,
	creds: Credentials = None,
	topic: str = None,
	badge: int = None,
	sound: str = None,
	content_available: bool = None,
	extra: dict = {},
	expiration: int = None,
	thread_id: str = None,
	loc_key: str = None,
	priority: int = None,
	collapse_id: str = None,
	mutable_content: bool = False,
	category: str = None,
	err_func: ErrFunc = None,
):
	"""
	Sends an APNS notification to one or more registration_ids.
	The registration_ids argument needs to be a list.

	Note that if set alert should always be a string. If it is not set,
	it won"t be included in the notification. You will need to pass None
	to this for silent notifications.

	:param registration_ids: A list of the registration_ids to send to
	:param alert: The alert message to send
	:param application_id: The application_id to use
	:param creds: The credentials to use
	:param mutable_content: If True, the "mutable-content" flag will be set to 1.
	                    This allows the app's Notification Service Extension to modify
	                    the notification before it is displayed.
	:param category: The category identifier for actionable notifications.
	                 This should match a category identifier defined in the app's
	                 Notification Content Extension or UNNotificationCategory configuration.
	                 It allows the app to display custom actions with the notification.
	:param content_available: If True the `content-available` flag will be set to 1, allowing the app to be woken up in the background
	"""
	try:
		topic = get_manager().get_apns_topic(application_id)
		results: Dict[str, str] = {}
		inactive_tokens = []

		responses = asyncio.run(
			_send_bulk_request(
				registration_ids=registration_ids,
				alert=alert,
				application_id=application_id,
				creds=creds,
				topic=topic,
				badge=badge,
				sound=sound,
				content_available=content_available,
				extra=extra,
				expiration=expiration,
				thread_id=thread_id,
				loc_key=loc_key,
				priority=priority,
				collapse_id=collapse_id,
				mutable_content=mutable_content,
				category=category,
				err_func=err_func,
			)
		)

		results = {}
		errors = []
		for registration_id, result in responses:
			results[registration_id] = (
				"Success" if result.is_successful else result.description
			)
			if not result.is_successful:
				errors.append(result.description)
				if result.description in [
					"Unregistered",
					"BadDeviceToken",
					"DeviceTokenNotForTopic",
				]:
					inactive_tokens.append(registration_id)

		if len(inactive_tokens) > 0:
			models.APNSDevice.objects.filter(
				registration_id__in=inactive_tokens
			).update(active=False)

		if len(errors) > 0:
			msg = "One or more errors failed with errors: {}".format(", ".join(errors))
			raise APNSError(msg)

		return results

	except ConnectionError as e:
		raise APNSServerError(status=e.__class__.__name__)


async def _send_bulk_request(
	registration_ids: list[str],
	alert: Union[str, Alert],
	application_id: str = None,
	creds: Credentials = None,
	topic: str = None,
	badge: int = None,
	sound: str = None,
	content_available: bool = None,
	extra: dict = {},
	expiration: int = None,
	thread_id: str = None,
	loc_key: str = None,
	priority: int = None,
	collapse_id: str = None,
	mutable_content: bool = False,
	category: str = None,
	err_func: ErrFunc = None,
):
	client = _create_client(
		creds=creds, application_id=application_id, topic=topic, err_func=err_func
	)

	aps_kwargs = {}
	if mutable_content:
		aps_kwargs["mutable-content"] = 1
	if category:
		aps_kwargs["category"] = category
	if content_available:
		aps_kwargs["content-available"] = 1

	requests = [
		_create_notification_request_from_args(
			registration_id,
			alert,
			badge=badge,
			sound=sound,
			extra=extra,
			expiration=expiration,
			thread_id=thread_id,
			loc_key=loc_key,
			priority=priority,
			collapse_id=collapse_id,
			aps_kwargs=aps_kwargs,
		)
		for registration_id in registration_ids
	]

	send_requests = [_send_request(client, request) for request in requests]
	return await asyncio.gather(*send_requests)


async def _send_request(apns, request):
	try:
		res = await asyncio.wait_for(apns.send_notification(request), timeout=1)
		return request.device_token, res
	except asyncio.TimeoutError:
		return request.device_token, NotificationResult(
			notification_id=request.notification_id,
			status="failed",
			description="TimeoutError",
		)
	except:
		return request.device_token, NotificationResult(
			notification_id=request.notification_id,
			status="failed",
			description="CommunicationError",
		)
