"""
Google Cloud Messaging
Previously known as C2DM
Documentation is available on the Android Developer website:
https://developer.android.com/google/gcm/index.html
"""

import json
from .models import GCMDevice


try:
	from urllib.request import Request, urlopen
	from urllib.parse import urlencode
except ImportError:
	# Python 2 support
	from urllib2 import Request, urlopen
	from urllib import urlencode

from django.core.exceptions import ImproperlyConfigured
from . import NotificationError
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


class GCMError(NotificationError):
	pass


def _chunks(l, n):
	"""
	Yield successive chunks from list \a l with a minimum size \a n
	"""
	for i in range(0, len(l), n):
		yield l[i:i + n]


def _gcm_send(data, content_type):
	key = SETTINGS.get("GCM_API_KEY")
	if not key:
		raise ImproperlyConfigured('You need to set PUSH_NOTIFICATIONS_SETTINGS["GCM_API_KEY"] to send messages through GCM.')

	headers = {
		"Content-Type": content_type,
		"Authorization": "key=%s" % (key),
		"Content-Length": str(len(data)),
	}

	request = Request(SETTINGS["GCM_POST_URL"], data, headers)
	return urlopen(request).read().decode("utf-8")


def _gcm_send_plain(registration_id, data, **kwargs):
	"""
	Sends a GCM notification to a single registration_id or to a topic (If "topic" included in the kwargs).
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	gcm_send_bulk_message() with a list of registration_ids
	"""

	values = {"registration_id": registration_id} if registration_id else {}

	for k, v in data.items():
		values["data.%s" % (k)] = v.encode("utf-8")

	for k, v in kwargs.items():
		if v:
			if isinstance(v, bool):
				# Encode bools into ints
				v = 1
			values[k] = v

	data = urlencode(sorted(values.items())).encode("utf-8")  # sorted items for tests

	result = _gcm_send(data, "application/x-www-form-urlencoded;charset=UTF-8")

	# Information about handling response from Google docs (https://developers.google.com/cloud-messaging/http):
	# If first line starts with id, check second line:
	# If second line starts with registration_id, gets its value and replace the registration tokens in your
	# server database. Otherwise, get the value of Error

	if result.startswith("id"):
		lines = result.split("\n")
		if len(lines) > 1 and lines[1].startswith("registration_id"):
			new_id = lines[1].split("=")[-1]
			_gcm_handle_canonical_id(new_id, registration_id)

	elif result.startswith("Error="):
		if result in ("Error=NotRegistered", "Error=InvalidRegistration"):
			# Deactivate the problematic device
			device = GCMDevice.objects.filter(registration_id=values["registration_id"])
			device.update(active=0)
			return result

		raise GCMError(result)

	return result


def _gcm_send_json(registration_ids, data, **kwargs):
	"""
	Sends a GCM notification to one or more registration_ids. The registration_ids
	needs to be a list.
	This will send the notification as json data.
	"""

	values = {"registration_ids": registration_ids}

	if data is not None:
		values["data"] = data

	for k, v in kwargs.items():
		if v:
			values[k] = v

	data = json.dumps(values, separators=(",", ":"), sort_keys=True).encode("utf-8")  # keys sorted for tests

	response = json.loads(_gcm_send(data, "application/json"))
	if response["failure"] or response["canonical_ids"]:
		ids_to_remove, old_new_ids = [], []
		throw_error = False
		for index, result in enumerate(response["results"]):
			error = result.get("error")
			if error:
				# Information from Google docs (https://developers.google.com/cloud-messaging/http)
				# If error is NotRegistered or InvalidRegistration, then we will deactivate devices because this
				# registration ID is no more valid and can't be used to send messages, otherwise raise error
				if error in ("NotRegistered", "InvalidRegistration"):
					ids_to_remove.append(registration_ids[index])
				else:
					throw_error = True

			# If registration_id is set, replace the original ID with the new value (canonical ID) in your
			# server database. Note that the original ID is not part of the result, so you need to obtain it
			# from the list of registration_ids passed in the request (using the same index).
			new_id = result.get("registration_id")
			if new_id:
				old_new_ids.append((registration_ids[index], new_id))

		if ids_to_remove:
			removed = GCMDevice.objects.filter(registration_id__in=ids_to_remove)
			removed.update(active=0)

		for old_id, new_id in old_new_ids:
			_gcm_handle_canonical_id(new_id, old_id)

		if throw_error:
			raise GCMError(response)
	return response


def _gcm_handle_canonical_id(canonical_id, current_id):
	"""
	Handle situation when GCM server response contains canonical ID
	"""
	if GCMDevice.objects.filter(registration_id=canonical_id, active=True).exists():
		GCMDevice.objects.filter(registration_id=current_id).update(active=False)
	else:
		GCMDevice.objects.filter(registration_id=current_id).update(registration_id=canonical_id)


def gcm_send_message(registration_id, data, **kwargs):
	"""
	Sends a GCM notification to a single registration_id.

	If sending multiple notifications, it is more efficient to use
	gcm_send_bulk_message() with a list of registration_ids

	A reference of extra keyword arguments sent to the server is available here:
	https://developers.google.com/cloud-messaging/server-ref#downstream
	"""

	if registration_id:
		return _gcm_send_plain(registration_id, data, **kwargs)


def gcm_send_bulk_message(registration_ids, data, **kwargs):
	"""
	Sends a GCM notification to one or more registration_ids. The registration_ids
	needs to be a list.
	This will send the notification as json data.

	A reference of extra keyword arguments sent to the server is available here:
	https://developers.google.com/cloud-messaging/server-ref#downstream
	"""

	# GCM only allows up to 1000 reg ids per bulk message
	# https://developer.android.com/google/gcm/gcm.html#request
	if registration_ids:
		max_recipients = SETTINGS.get("GCM_MAX_RECIPIENTS")
		if len(registration_ids) > max_recipients:
			ret = []
			for chunk in _chunks(registration_ids, max_recipients):
				ret.append(_gcm_send_json(chunk, data, **kwargs))
			return ret

		return _gcm_send_json(registration_ids, data, **kwargs)
