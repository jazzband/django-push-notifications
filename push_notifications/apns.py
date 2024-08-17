"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/content/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/APNSOverview.html
"""

import asyncio
import contextlib
import tempfile
import time

import aioapns
from aioapns.common import APNS_RESPONSE_CODE, PRIORITY_HIGH, PRIORITY_NORMAL
from asgiref.sync import async_to_sync

from . import models
from .conf import get_manager
from .exceptions import APNSError, APNSServerError, APNSUnsupportedPriority


SUCCESS_RESULT = "Success"
UNREGISTERED_RESULT = "Unregistered"


@contextlib.contextmanager
def _apns_path_for_cert(cert):
	if cert is None:
		yield None
	with tempfile.NamedTemporaryFile("w") as cert_file:
		cert_file.write(cert)
		cert_file.flush()
		yield cert_file.name


def _apns_create_client(application_id=None):
	cert = None
	key_path = None
	key_id = None
	team_id = None

	if not get_manager().has_auth_token_creds(application_id):
		cert = get_manager().get_apns_certificate(application_id)
		with _apns_path_for_cert(cert) as cert_path:
			client = aioapns.APNs(
				client_cert=cert_path,
				team_id=team_id,
				topic=get_manager().get_apns_topic(application_id),
				use_sandbox=get_manager().get_apns_use_sandbox(application_id),
			)
	else:
		key_path, key_id, team_id = get_manager().get_apns_auth_creds(application_id)
		client = aioapns.APNs(
			key=key_path,
			key_id=key_id,
			team_id=team_id,
			topic=get_manager().get_apns_topic(application_id),
			use_sandbox=get_manager().get_apns_use_sandbox(application_id),
		)

	return client


def _apns_prepare(
	token,
	alert,
	application_id=None,
	badge=None,
	sound=None,
	category=None,
	content_available=False,
	action_loc_key=None,
	loc_key=None,
	loc_args=[],
	extra={},
	mutable_content=False,
	thread_id=None,
	url_args=None,
):
	if action_loc_key or loc_key or loc_args:
		alert_payload = {
			"body": alert if alert else {},
			"body_localized_key": loc_key,
			"body_localized_args": loc_args,
			"action_localized_key": action_loc_key,
		}
	else:
		alert_payload = alert

	if callable(badge):
		badge = badge(token)

	return {
		"alert": alert_payload,
		"badge": badge,
		"sound": sound,
		"category": category,
		"url_args": url_args,
		"custom": extra,
		"thread_id": thread_id,
		"content_available": content_available,
		"mutable_content": mutable_content,
	}


@async_to_sync
async def _apns_send(
	registration_ids,
	alert,
	application_id=None,
	*,
	priority=None,
	expiration=None,
	collapse_id=None,
	**kwargs,
):
	"""Make calls to APNs for each device token (registration_id) provided.

	Since the underlying library (aioapns) is asynchronous, we are
	taking advantage of that here and making the requests in parallel.
	"""
	client = _apns_create_client(application_id=application_id)

	# if expiration isn't specified use 1 month from now
	# converting to ttl for underlying library
	if expiration:
		time_to_live = expiration - int(time.time())
	else:
		time_to_live = 2592000

	if priority is not None:
		if str(priority) not in [PRIORITY_HIGH, PRIORITY_NORMAL]:
			raise APNSUnsupportedPriority(f"Unsupported priority {priority}")

	# track which device token belongs to each coroutine.
	# this allows us to stitch the results back together later
	coro_registration_ids = {}
	for registration_id in set(registration_ids):
		coro = client.send_notification(
			aioapns.NotificationRequest(
				device_token=registration_id,
				message={"aps": _apns_prepare(registration_id, alert, **kwargs)},
				time_to_live=time_to_live,
				priority=priority,
				collapse_key=collapse_id,
			)
		)
		coro_registration_ids[asyncio.create_task(coro)] = registration_id

	# run all of the tasks. this will resolve once all requests are complete
	done, _ = await asyncio.wait(coro_registration_ids.keys())

	# recombine task results with their device tokens
	results = {}
	for coro in done:
		registration_id = coro_registration_ids[coro]
		result = await coro
		if result.is_successful:
			results[registration_id] = SUCCESS_RESULT
		else:
			results[registration_id] = result.description

	return results


def apns_send_message(registration_id, alert, application_id=None, **kwargs):
	"""
	Sends an APNS notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	apns_send_bulk_message()

	Note that if set alert should always be a string. If it is not set,
	it won"t be included in the notification. You will need to pass None
	to this for silent notifications.
	"""

	results = _apns_send(
		[registration_id], alert, application_id=application_id, **kwargs
	)
	result = results[registration_id]

	if result == SUCCESS_RESULT:
		return
	if result == UNREGISTERED_RESULT:
		models.APNSDevice.objects.filter(registration_id=registration_id).update(
			active=False
		)
	raise APNSServerError(status=result)


def apns_send_bulk_message(registration_ids, alert, application_id=None, **kwargs):
	"""
	Sends an APNS notification to one or more registration_ids.
	The registration_ids argument needs to be a list.

	Note that if set alert should always be a string. If it is not set,
	it won"t be included in the notification. You will need to pass None
	to this for silent notifications.
	"""

	results = _apns_send(
		registration_ids, alert, application_id=application_id, **kwargs
	)
	inactive_tokens = [
		token for token, result in results.items() if result == UNREGISTERED_RESULT
	]
	models.APNSDevice.objects.filter(registration_id__in=inactive_tokens).update(
		active=False
	)
	return results
