"""
Google Cloud Messaging
Previously known as C2DM
Documentation is available on the Android Developer website:
https://developer.android.com/google/gcm/index.html
"""

import json

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
	response = urlopen(request)
	result = response.read().decode("utf-8")

	# FIXME: broken for bulk results
	if result.startswith("Error="):
		raise GCMError(result)

	return result


def gcm_send_message(registration_id, data, collapse_key=None, delay_while_idle=False):
	"""
	Sends a GCM notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	gcm_send_bulk_message() with a list of registration_ids
	"""

	values = {"registration_id": registration_id}

	if collapse_key:
		values["collapse_key"] = collapse_key

	for k, v in data.items():
		values["data.%s" % (k)] = v.encode("utf-8")

	data = urlencode(values).encode("utf-8")
	return _gcm_send(data, "application/x-www-form-urlencoded;charset=UTF-8")


def gcm_send_bulk_message(registration_ids, data, collapse_key=None, delay_while_idle=False):
	"""
	Sends a GCM notification to one or more registration_ids. The registration_ids
	needs to be a list.
	This will send the notification as json data.
	"""

	# GCM only allows up to 1000 reg ids per bulk message
	# https://developer.android.com/google/gcm/gcm.html#request
	max_recipients = SETTINGS.get("GCM_MAX_RECIPIENTS")
	if len(registration_ids) > max_recipients:
		ret = []
		for chunk in _chunks(registration_ids, max_recipients):
			ret.append(gcm_send_bulk_message(chunk, data, collapse_key, delay_while_idle))
		return "\n".join(ret)

	values = {"registration_ids": registration_ids}

	if data is not None:
		values["data"] = data

	if collapse_key:
		values["collapse_key"] = collapse_key

	if delay_while_idle:
		values["delay_while_idle"] = delay_while_idle

	data = json.dumps(values, separators=(",", ":")).encode("utf-8")
	return _gcm_send(data, "application/json")
