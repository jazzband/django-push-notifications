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
	Sends a GCM notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	gcm_send_bulk_message() with a list of registration_ids
	"""

	values = {"registration_id": registration_id}

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

	if result.startswith("Error="):
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

	result = json.loads(_gcm_send(data, "application/json"))
	if result["failure"]:
		ids_to_remove = []
		throw_error = 0
		for index, er in enumerate(result["results"]):
			if er.get("error", "none") in ("NotRegistered", "InvalidRegistration"):
				ids_to_remove.append(values["registration_ids"][index])
			elif er.get("error", "none") is not "none":
				throw_error = 1
		if ids_to_remove:
			removed = GCMDevice.objects.filter(registration_id__in=ids_to_remove)
			removed.update(active=0)
		if throw_error:
			raise GCMError(result)
	return result


def gcm_send_message(registration_id, data, **kwargs):
	"""
	Sends a GCM notification to a single registration_id.

	This will send the notification as form data if possible, otherwise it will
	fall back to json data.

	If sending multiple notifications, it is more efficient to use
	gcm_send_bulk_message() with a list of registration_ids

	A reference of extra keyword arguments sent to the server is available here:
	https://developers.google.com/cloud-messaging/server-ref#downstream
	"""

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
	max_recipients = SETTINGS.get("GCM_MAX_RECIPIENTS")
	if len(registration_ids) > max_recipients:
		ret = []
		for chunk in _chunks(registration_ids, max_recipients):
			ret.append(_gcm_send_json(chunk, data, **kwargs))
		return ret

	return _gcm_send_json(registration_ids, data, **kwargs)
