"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/ApplePushService.html
"""

import json
import ssl
import struct
import socket
import time
from contextlib import closing
from binascii import unhexlify
from django.core.exceptions import ImproperlyConfigured
from . import NotificationError
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


class APNSError(NotificationError):
	pass


class APNSServerError(APNSError):
	def __init__(self, status, identifier):
		super(APNSServerError, self).__init__(status, identifier)
		self.status = status
		self.identifier = identifier


class APNSDataOverflow(APNSError):
	pass


APNS_MAX_NOTIFICATION_SIZE = 256


def _apns_create_socket():
	certfile = SETTINGS.get("APNS_CERTIFICATE")
	if not certfile:
		raise ImproperlyConfigured(
			'You need to set PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] to send messages through APNS.'
		)

	try:
		with open(certfile, "r") as f:
			f.read()
	except Exception as e:
		raise ImproperlyConfigured("The APNS certificate file at %r is not readable: %s" % (certfile, e))

	sock = socket.socket()
	sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_SSLv3, certfile=certfile)
	sock.connect((SETTINGS["APNS_HOST"], SETTINGS["APNS_PORT"]))

	return sock


def _apns_pack_frame(token_hex, payload, identifier, expiration, priority):
	token = unhexlify(token_hex)
	# |COMMAND|FRAME-LEN|{token}|{payload}|{id:4}|{expiration:4}|{priority:1}
	frame_len = 3 * 5 + len(token) + len(payload) + 4 + 4 + 1  # 5 items, each 3 bytes prefix, then each item length
	frame_fmt = "!BIBH%ssBH%ssBHIBHIBHB" % (len(token), len(payload))
	frame = struct.pack(
		frame_fmt,
		2, frame_len,
		1, len(token), token,
		2, len(payload), payload,
		3, 4, identifier,
		4, 4, expiration,
		5, 1, priority)

	return frame


def _apns_check_errors(sock):
	timeout = SETTINGS["APNS_ERROR_TIMEOUT"]
	if timeout is None:
		return  # assume everything went fine!
	saved_timeout = sock.gettimeout()
	try:
		sock.settimeout(timeout)
		data = sock.recv(6)
		if data:
			command, status, identifier = struct.unpack("!BBI", data)
			# apple protocol says command is always 8. See http://goo.gl/ENUjXg
			assert command == 8, "Command must be 8!"
			if status != 0:
				raise APNSServerError(status, identifier)
	except socket.timeout:  # py3
		pass
	except ssl.SSLError as e:  # py2
		if "timed out" not in e.message:
			raise
	finally:
		sock.settimeout(saved_timeout)


def _apns_send(token, alert, badge=None, sound=None, content_available=False, action_loc_key=None, loc_key=None,
				loc_args=[], extra={}, identifier=0, expiration=None, priority=10, socket=None):
	data = {}
	aps_data = {}

	if action_loc_key or loc_key or loc_args:
		alert = {"body": alert} if alert else {}
		if action_loc_key:
			alert["action-loc-key"] = action_loc_key
		if loc_key:
			alert["loc-key"] = loc_key
		if loc_args:
			alert["loc-args"] = loc_args

	if alert is not None:
		aps_data["alert"] = alert

	if badge is not None:
		aps_data["badge"] = badge

	if sound is not None:
		aps_data["sound"] = sound

	if content_available:
		aps_data["content-available"] = 1

	data["aps"] = aps_data
	data.update(extra)

	# convert to json, avoiding unnecessary whitespace with separators
	json_data = json.dumps(data, separators=(",", ":")).encode("utf-8")

	if len(json_data) > APNS_MAX_NOTIFICATION_SIZE:
		raise APNSDataOverflow("Notification body cannot exceed %i bytes" % (APNS_MAX_NOTIFICATION_SIZE))

	# if expiration isn't specified use 1 month from now
	expiration_time = expiration if expiration is not None else int(time.time()) + 2592000

	frame = _apns_pack_frame(token, json_data, identifier, expiration_time, priority)

	if socket:
		socket.write(frame)
	else:
		with closing(_apns_create_socket()) as socket:
			socket.write(frame)
			_apns_check_errors(socket)


def apns_send_message(registration_id, alert, **kwargs):
	"""
	Sends an APNS notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	apns_send_bulk_message()

	Note that if set alert should always be a string. If it is not set,
	it won't be included in the notification. You will need to pass None
	to this for silent notifications.
	"""

	return _apns_send(registration_id, alert, **kwargs)


def apns_send_bulk_message(registration_ids, alert, **kwargs):
	"""
	Sends an APNS notification to one or more registration_ids.
	The registration_ids argument needs to be a list.

	Note that if set alert should always be a string. If it is not set,
	it won't be included in the notification. You will need to pass None
	to this for silent notifications.
	"""
	with closing(_apns_create_socket()) as socket:
		for identifier, registration_id in enumerate(registration_ids):
			_apns_send(registration_id, alert, identifier=identifier, socket=socket, **kwargs)
		_apns_check_errors(socket)
