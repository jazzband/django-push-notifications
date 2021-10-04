"""
Firebase Cloud Messaging
Previously known as GCM / C2DM
Documentation is available on the Firebase Developer website:
https://firebase.google.com/docs/cloud-messaging/
"""

import json

from django.core.exceptions import ImproperlyConfigured

from .compat import Request, urlopen
from .conf import get_manager
from .exceptions import GCMError
from .models import GCMDevice


# Valid keys for FCM messages. Reference:
# https://firebase.google.com/docs/cloud-messaging/http-server-ref
FCM_TARGETS_KEYS = [
	"to", "condition", "notification_key"
]
FCM_OPTIONS_KEYS = [
	"collapse_key", "priority", "content_available", "delay_while_idle", "time_to_live",
	"restricted_package_name", "dry_run", "mutable_content"
]
FCM_NOTIFICATIONS_PAYLOAD_KEYS = [
	"title", "body", "icon", "image", "sound", "badge", "color", "tag", "click_action",
	"body_loc_key", "body_loc_args", "title_loc_key", "title_loc_args", "android_channel_id"
]

def _chunks(l, n):
	"""
	Yield successive chunks from list \a l with a minimum size \a n
	"""
	for i in range(0, len(l), n):
		yield l[i:i + n]


def _gcm_send(data, content_type, application_id):
	key = get_manager().get_gcm_api_key(application_id)

	headers = {
		"Content-Type": content_type,
		"Authorization": "key=%s" % (key),
		"Content-Length": str(len(data)),
	}
	request = Request(get_manager().get_post_url("GCM", application_id), data, headers)
	return urlopen(
		request, timeout=get_manager().get_error_timeout("GCM", application_id)
	).read().decode("utf-8")


def _fcm_send(data, content_type, application_id):
	key = get_manager().get_fcm_api_key(application_id)

	headers = {
		"Content-Type": content_type,
		"Authorization": "key=%s" % (key),
		"Content-Length": str(len(data)),
	}
	request = Request(get_manager().get_post_url("FCM", application_id), data, headers)
	return urlopen(
		request, timeout=get_manager().get_error_timeout("FCM", application_id)
	).read().decode("utf-8")


def _cm_handle_response(registration_ids, response_data, cloud_type, application_id=None):
	response = response_data
	if response.get("failure") or response.get("canonical_ids"):
		ids_to_remove, old_new_ids = [], []
		throw_error = False
		for index, result in enumerate(response["results"]):
			error = result.get("error")
			if error:
				# https://firebase.google.com/docs/cloud-messaging/http-server-ref#error-codes
				# If error is NotRegistered or InvalidRegistration, then we will deactivate devices
				# because this registration ID is no more valid and can't be used to send messages,
				# otherwise raise error
				if error in ("NotRegistered", "InvalidRegistration"):
					ids_to_remove.append(registration_ids[index])
				else:
					throw_error = True
			result["original_registration_id"] = registration_ids[index]
			# If registration_id is set, replace the original ID with the new value (canonical ID)
			# in your server database. Note that the original ID is not part of the result, you need
			# to obtain it from the list of registration_ids in the request (using the same index).
			new_id = result.get("registration_id")
			if new_id:
				old_new_ids.append((registration_ids[index], new_id))

		if ids_to_remove:
			removed = GCMDevice.objects.filter(
				registration_id__in=ids_to_remove, cloud_message_type=cloud_type
			)
			removed.update(active=False)

		for old_id, new_id in old_new_ids:
			_cm_handle_canonical_id(new_id, old_id, cloud_type)

		if throw_error:
			raise GCMError(response)
	return response


def _cm_send_request(
	registration_ids, data, cloud_type="GCM", application_id=None,
	use_fcm_notifications=True, **kwargs
):
	"""
	Sends a FCM or GCM notification to one or more registration_ids as json data.
	The registration_ids needs to be a list.
	"""

	payload = {"registration_ids": registration_ids} if registration_ids else {}

	data = data.copy()

	# If using FCM, optionally autodiscovers notification related keys
	# https://firebase.google.com/docs/cloud-messaging/concept-options#notifications_and_data_messages
	if cloud_type == "FCM" and use_fcm_notifications:
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
			payload["notification"] = notification_payload

	if data:
		payload["data"] = data

	# Attach any additional non falsy keyword args (targets, options)
	# See ref : https://firebase.google.com/docs/cloud-messaging/http-server-ref#table1
	payload.update({
		k: v for k, v in kwargs.items() if v and (k in FCM_TARGETS_KEYS or k in FCM_OPTIONS_KEYS)
	})

	# Sort the keys for deterministic output (useful for tests)
	json_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

	# Sends requests and handles the response
	if cloud_type == "GCM":
		response = json.loads(_gcm_send(
			json_payload, "application/json", application_id=application_id
		))
	elif cloud_type == "FCM":
		response = json.loads(_fcm_send(
			json_payload, "application/json", application_id=application_id
		))
	else:
		raise ImproperlyConfigured("cloud_type must be FCM or GCM not %s" % str(cloud_type))
	return _cm_handle_response(registration_ids, response, cloud_type, application_id)


def _cm_handle_canonical_id(canonical_id, current_id, cloud_type):
	"""
	Handle situation when FCM server response contains canonical ID
	"""
	devices = GCMDevice.objects.filter(cloud_message_type=cloud_type)
	if devices.filter(registration_id=canonical_id, active=True).exists():
		devices.filter(registration_id=current_id).update(active=False)
	else:
		devices.filter(registration_id=current_id).update(registration_id=canonical_id)


def send_message(registration_ids, data, cloud_type, application_id=None, **kwargs):
	"""
	Sends a FCM (or GCM) notification to one or more registration_ids. The registration_ids
	can be a list or a single string. This will send the notification as json data.

	A reference of extra keyword arguments sent to the server is available here:
	https://firebase.google.com/docs/cloud-messaging/http-server-ref#table1
	"""
	if cloud_type in ("FCM", "GCM"):
		max_recipients = get_manager().get_max_recipients(cloud_type, application_id)
	else:
		raise ImproperlyConfigured("cloud_type must be FCM or GCM not %s" % str(cloud_type))

	# Checks for valid recipient
	if registration_ids is None and "/topics/" not in kwargs.get("to", ""):
		return

	# Bundles the registration_ids in an list if only one is sent
	if not isinstance(registration_ids, list):
		registration_ids = [registration_ids] if registration_ids else None

	# FCM only allows up to 1000 reg ids per bulk message
	# https://firebase.google.com/docs/cloud-messaging/server#http-request
	if registration_ids:
		ret = []
		for chunk in _chunks(registration_ids, max_recipients):
			ret.append(_cm_send_request(
				chunk, data, cloud_type=cloud_type, application_id=application_id, **kwargs
			))
		return ret[0] if len(ret) == 1 else ret
	else:
		return _cm_send_request(None, data, cloud_type=cloud_type, **kwargs)


send_bulk_message = send_message
