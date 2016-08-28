"""
Firebace Cloud Message
Previously known as C2DM
Documentation is available on the Android Developer website:
https://developer.android.com/google/fcm/index.html
"""

import json
from .models import FCMDevice

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


class FCMError(NotificationError):
	pass


PRIORITY_HIGHT = 'high'
PRIORITY_NORMAL = 'normal'


class FCMNotification(object):
	def __init__(self, body=None, title=None, icon=None, click_action=None, sound='default', **kwargs):
		kwargs = kwargs.update(body=body, title=title, icon=icon, click_action=None, sound=sound)
		self.data = kwargs


def _chunks(l, n):
	"""
Yield successive chunks from list \a l with a minimum size \a n
"""
	for i in range(0, len(l), n):
		yield l[i:i + n]


def _fcm_send_json(params):
	params = json.dumps(params, separators=(",", ":"), sort_keys=True).encode("utf-8")

	key = SETTINGS.get("FCM_API_KEY")
	if not key:
		raise ImproperlyConfigured(
			'You need to set PUSH_NOTIFICATIONS_SETTINGS["FCM_API_KEY"] to send messages through FCM.'
		)

	headers = {
		'UserAgent': "FCM-Server",
		"Content-Type": 'application/json',
		"Authorization": "key=%s" % (key),
		"Content-Length": str(len(params)),
	}
	request = Request(SETTINGS["FCM_POST_URL"], params, headers)
	return urlopen(request, timeout=SETTINGS["FCM_ERROR_TIMEOUT"]).read().decode("utf-8")


def _fcm_send_message(params):
	# Sort the keys for deterministic output (useful for tests)
	response = json.loads(_fcm_send_json(params))

	if response["failure"] or response["canonical_ids"]:
		ids_to_remove, old_new_ids = [], []
		throw_error = False
		for index, result in enumerate(response["results"]):
			error = result.get("error")
			if error:
				# Information from Google docs
				# https://developers.google.com/cloud-messaging/http
				# If error is NotRegistered or InvalidRegistration,
				# then we will deactivate devices because this
				# registration ID is no more valid and can't be used
				# to send messages, otherwise raise error
				if error in ("NotRegistered", "InvalidRegistration"):
					ids_to_remove.append(registration_ids[index])
				else:
					throw_error = True

			# If registration_id is set, replace the original ID with
			# the new value (canonical ID) in your server database.
			# Note that the original ID is not part of the result, so
			# you need to obtain it from the list of registration_ids
			# passed in the request (using the same index).
			new_id = result.get("registration_id")
			if new_id:
				old_new_ids.append((registration_ids[index], new_id))

		if ids_to_remove:
			removed = FCMDevice.objects.filter(registration_id__in=ids_to_remove)
			removed.update(active=0)

		for old_id, new_id in old_new_ids:
			_fcm_handle_canonical_id(new_id, old_id)

		if throw_error:
			raise FCMError(response)
	return response


def _fcm_handle_canonical_id(canonical_id, current_id):
	"""
Handle situation when FCM server response contains canonical ID
"""
	if FCMDevice.objects.filter(registration_id=canonical_id, active=True).exists():
		FCMDevice.objects.filter(registration_id=current_id).update(active=False)
	else:
		FCMDevice.objects.filter(registration_id=current_id).update(registration_id=canonical_id)


def fcm_send_message(to,
					 data=None,
					 notification=None,
					 priority=PRIORITY_NORMAL,
					 **kwargs):
	# if isinstance(to, list):
	# 	max_recipients = SETTINGS.get("FCM_MAX_RECIPIENTS")
	# 	if len(to) > max_recipients:
	# 		ret = []
	# 		for chunk in _chunks(to, max_recipients):
	# 			ret.append(fcm_send_message(chunk, data, notification, priority, **kwargs))
	# 		return ret
	if isinstance(to, list):
		ret = []
		for id in to:
			ret.append(fcm_send_message(id, data, notification, priority, **kwargs))
		return ret
	if notification:
		if not isinstance(notification, dict) and not isinstance(notification, FCMNotification):
			raise TypeError('Notification has to be a FCMNotification object or a dict.')

	values = dict(to=to)

	if data:
		values['data'] = data

	if notification:
		if isinstance(notification, FCMNotification):
			values['notification'] = notification.data
		else:
			values['notification'] = notification

	if priority:
		values['priority'] = priority

	for k, v in kwargs.items():
		if v:
			values[k] = v

	return _fcm_send_message(values)


def fcm_send_bulk_message(to,
						  data=None,
						  notification=None,
						  priority=PRIORITY_NORMAL,
						  **kwargs):
	return fcm_send_message(to, data, notification, priority, **kwargs)
