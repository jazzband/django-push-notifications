"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/ApplePushService.html
"""

import codecs
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


def _check_certificate(ss):
	mode = "start"
	for s in ss.split("\n"):
		if mode == "start":
			if "BEGIN RSA PRIVATE KEY" in s:
				mode = "key"
		elif mode == "key":
			if "END RSA PRIVATE KEY" in s:
				mode = "end"
				break
			elif s.startswith("Proc-Type") and "ENCRYPTED" in s:
				raise Exception("The certificate private key should not be encrypted")
	if mode != "end":
		raise Exception("The certificate doesn't contain a private key")


def _apns_create_socket(address_tuple, certfile=None):
	certfile = certfile or SETTINGS.get("APNS_CERTIFICATE")
	if not certfile:
		raise ImproperlyConfigured(
			'You need to set PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] to send messages through APNS.'
		)

	try:
		with open(certfile, "r") as f:
			content = f.read()
	except Exception as e:
		raise ImproperlyConfigured("The APNS certificate file at %r is not readable: %s" % (certfile, e))

	try:
		_check_certificate(content)
	except Exception as e:
		raise ImproperlyConfigured("The APNS certificate file at %r is unusable: %s" % (certfile, e))

	ca_certs = SETTINGS.get("APNS_CA_CERTIFICATES")

	sock = socket.socket()
	sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1, certfile=certfile, ca_certs=ca_certs)
	sock.connect(address_tuple)

	return sock


def _apns_create_socket_to_push(certfile=None):
	return _apns_create_socket((SETTINGS["APNS_HOST"], SETTINGS["APNS_PORT"]), certfile)


def _apns_create_socket_to_feedback(certfile=None):
	return _apns_create_socket((SETTINGS["APNS_FEEDBACK_HOST"], SETTINGS["APNS_FEEDBACK_PORT"]), certfile)


def _apns_pack_frame(token_hex, payload, identifier, expiration, priority):
	token = unhexlify(token_hex)
	# |COMMAND|FRAME-LEN|{token}|{payload}|{id:4}|{expiration:4}|{priority:1}
	# 5 items, each 3 bytes prefix, then each item length
	frame_len = 3 * 5 + len(token) + len(payload) + 4 + 4 + 1
	frame_fmt = "!BIBH%ssBH%ssBHIBHIBHB" % (len(token), len(payload))
	frame = struct.pack(
		frame_fmt,
		2, frame_len,
		1, len(token), token,
		2, len(payload), payload,
		3, 4, identifier,
		4, 4, expiration,
		5, 1, priority
	)

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
	except socket.timeout:  # py3, see http://bugs.python.org/issue10272
		pass
	except ssl.SSLError as e:  # py2
		if "timed out" not in e.message:
			raise
	finally:
		sock.settimeout(saved_timeout)


def _apns_send(
	token, alert, badge=None, sound=None, category=None, content_available=False,
	action_loc_key=None, loc_key=None, loc_args=[], extra={}, identifier=0,
	expiration=None, priority=10, socket=None, certfile=None
):
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

	if category is not None:
		aps_data["category"] = category

	if content_available:
		aps_data["content-available"] = 1

	data["aps"] = aps_data
	data.update(extra)

	# convert to json, avoiding unnecessary whitespace with separators (keys sorted for tests)
	json_data = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")

	max_size = SETTINGS["APNS_MAX_NOTIFICATION_SIZE"]
	if len(json_data) > max_size:
		raise APNSDataOverflow("Notification body cannot exceed %i bytes" % (max_size))

	# if expiration isn't specified use 1 month from now
	expiration_time = expiration if expiration is not None else int(time.time()) + 2592000

	frame = _apns_pack_frame(token, json_data, identifier, expiration_time, priority)

	if socket:
		socket.write(frame)
	else:
		with closing(_apns_create_socket_to_push(certfile)) as socket:
			socket.write(frame)
			_apns_check_errors(socket)


def _apns_read_and_unpack(socket, data_format):
	length = struct.calcsize(data_format)
	data = socket.recv(length)
	if data:
		return struct.unpack_from(data_format, data, 0)
	else:
		return None


def _apns_receive_feedback(socket):
	expired_token_list = []

	# read a timestamp (4 bytes) and device token length (2 bytes)
	header_format = "!LH"
	has_data = True
	while has_data:
		try:
			# read the header tuple
			header_data = _apns_read_and_unpack(socket, header_format)
			if header_data is not None:
				timestamp, token_length = header_data
				# Unpack format for a single value of length bytes
				token_format = "%ss" % token_length
				device_token = _apns_read_and_unpack(socket, token_format)
				if device_token is not None:
					# _apns_read_and_unpack returns a tuple, but
					# it's just one item, so get the first.
					expired_token_list.append((timestamp, device_token[0]))
			else:
				has_data = False
		except socket.timeout:  # py3, see http://bugs.python.org/issue10272
			pass
		except ssl.SSLError as e:  # py2
			if "timed out" not in e.message:
				raise

	return expired_token_list


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

	_apns_send(registration_id, alert, **kwargs)


def apns_send_bulk_message(registration_ids, alert, **kwargs):
	"""
	Sends an APNS notification to one or more registration_ids.
	The registration_ids argument needs to be a list.

	Note that if set alert should always be a string. If it is not set,
	it won't be included in the notification. You will need to pass None
	to this for silent notifications.
	"""
	certfile = kwargs.get("certfile", None)
	with closing(_apns_create_socket_to_push(certfile)) as socket:
		for identifier, registration_id in enumerate(registration_ids):
			_apns_send(registration_id, alert, identifier=identifier, socket=socket, **kwargs)
		_apns_check_errors(socket)


def apns_fetch_inactive_ids(certfile=None):
	"""
	Queries the APNS server for id's that are no longer active since
	the last fetch
	"""
	with closing(_apns_create_socket_to_feedback(certfile)) as socket:
		inactive_ids = []
		# Maybe we should have a flag to return the timestamp?
		# It doesn't seem that useful right now, though.
		for ts, registration_id in _apns_receive_feedback(socket):
			inactive_ids.append(codecs.encode(registration_id, "hex_codec"))
		return inactive_ids
