"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/ApplePushService.html
"""

import json
import ssl
import struct
from binascii import unhexlify
from socket import socket
from django.core.exceptions import ImproperlyConfigured
from . import NotificationError
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


class APNSError(NotificationError):
	pass


class APNSDataOverflow(APNSError):
	pass

APNS_MAX_NOTIFICATION_SIZE = 256


def _apns_create_socket():
	sock = socket()
	certfile = SETTINGS.get("APNS_CERTIFICATE")
	if not certfile:
		raise ImproperlyConfigured(
			'You need to set PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] to send messages through APNS.'
		)

	try:
		f = open(certfile, "r")
		f.read()
		f.close()
	except Exception as e:
		raise ImproperlyConfigured("The APNS certificate file at %r is not readable: %s" % (certfile, e))

	sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_SSLv3, certfile=certfile)
	sock.connect((SETTINGS["APNS_HOST"], SETTINGS["APNS_PORT"]))

	return sock


def _apns_pack_message(token, data):
	format = "!cH32sH%ds" % (len(data))
	return struct.pack(format, b"\0", 32, unhexlify(token), len(data), data)


def _apns_send(token, alert, badge=0, sound="chime", content_available=False, action_loc_key=None, loc_key=None, loc_args=[], extra={}, socket=None):
	data = {}
	apns_data = {}

	if action_loc_key or loc_key or loc_args:
		alert = {"body": alert}
		if action_loc_key:
			alert["action-loc-key"] = action_loc_key
		if loc_key:
			alert["loc-key"] = loc_key
		if loc_args:
			alert["loc-args"] = loc_args

	if alert is not None:
		apns_data["alert"] = alert

	if badge:
		apns_data["badge"] = badge

	if sound:
		apns_data["sound"] = sound

	if content_available:
		apns_data["content-available"] = 1

	data["aps"] = apns_data
	data.update(extra)

	# convert to json, avoiding unnecessary whitespace with separators
	data = json.dumps(data, separators=(",", ":"))

	if len(data) > APNS_MAX_NOTIFICATION_SIZE:
		raise APNSDataOverflow("Notification body cannot exceed %i bytes" % (APNS_MAX_NOTIFICATION_SIZE))

	data = _apns_pack_message(token, data)

	if socket:
		socket.write(data)
	else:
		socket = _apns_create_socket()
		socket.write(data)
		socket.close()


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
	socket = _apns_create_socket()
	for registration_id in registration_ids:
		_apns_send(registration_id, alert, socket=socket, **kwargs)

	socket.close()
