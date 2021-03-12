"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/content/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/APNSOverview.html
"""

import time

from apns2 import client as apns2_client
from apns2 import credentials as apns2_credentials
from apns2 import errors as apns2_errors
from apns2 import payload as apns2_payload

from . import models
from .conf import get_manager
from .exceptions import APNSError, APNSUnsupportedPriority, APNSServerError


def _apns_create_socket(creds=None, application_id=None):
	if creds is None:
		if not get_manager().has_auth_token_creds(application_id):
			cert = get_manager().get_apns_certificate(application_id)
			creds = apns2_credentials.CertificateCredentials(cert)
		else:
			keyPath, keyId, teamId = get_manager().get_apns_auth_creds(application_id)
			# No use getting a lifetime because this credential is
			# ephemeral, but if you're looking at this to see how to
			# create a credential, you could also pass the lifetime and
			# algorithm. Neither of those settings are exposed in the
			# settings API at the moment.
			creds = creds or apns2_credentials.TokenCredentials(keyPath, keyId, teamId)
	client = apns2_client.APNsClient(
		creds,
		use_sandbox=get_manager().get_apns_use_sandbox(application_id),
		use_alternative_port=get_manager().get_apns_use_alternative_port(application_id)
	)
	client.connect()
	return client


def _apns_prepare(
	token, alert, application_id=None, badge=None, sound=None, category=None,
	content_available=False, action_loc_key=None, loc_key=None, loc_args=[],
	extra={}, mutable_content=False, thread_id=None, url_args=None):
		if action_loc_key or loc_key or loc_args:
			apns2_alert = apns2_payload.PayloadAlert(
				body=alert if alert else {}, body_localized_key=loc_key,
				body_localized_args=loc_args, action_localized_key=action_loc_key)
		else:
			apns2_alert = alert

		if callable(badge):
			badge = badge(token)

		return apns2_payload.Payload(
			alert=apns2_alert, badge=badge, sound=sound, category=category,
			url_args=url_args, custom=extra, thread_id=thread_id,
			content_available=content_available, mutable_content=mutable_content)


def _apns_send(
	registration_id, alert, batch=False, application_id=None, creds=None, **kwargs
):
	client = _apns_create_socket(creds=creds, application_id=application_id)

	notification_kwargs = {}

	# if expiration isn"t specified use 1 month from now
	notification_kwargs["expiration"] = kwargs.pop("expiration", None)
	if not notification_kwargs["expiration"]:
		notification_kwargs["expiration"] = int(time.time()) + 2592000

	priority = kwargs.pop("priority", None)
	if priority:
		try:
			notification_kwargs["priority"] = apns2_client.NotificationPriority(str(priority))
		except ValueError:
			raise APNSUnsupportedPriority("Unsupported priority %d" % (priority))

	notification_kwargs["collapse_id"] = kwargs.pop("collapse_id", None)

	if batch:
		data = [apns2_client.Notification(
			token=rid, payload=_apns_prepare(rid, alert, **kwargs)) for rid in registration_id]
		# returns a dictionary mapping each token to its result. That
		# result is either "Success" or the reason for the failure.
		return client.send_notification_batch(
			data, get_manager().get_apns_topic(application_id=application_id),
			**notification_kwargs
		)

	data = _apns_prepare(registration_id, alert, **kwargs)
	client.send_notification(
		registration_id, data,
		get_manager().get_apns_topic(application_id=application_id),
		**notification_kwargs
	)


def apns_send_message(registration_id, alert, application_id=None, creds=None, **kwargs):
	"""
	Sends an APNS notification to a single registration_id.
	This will send the notification as form data.
	If sending multiple notifications, it is more efficient to use
	apns_send_bulk_message()

	Note that if set alert should always be a string. If it is not set,
	it won"t be included in the notification. You will need to pass None
	to this for silent notifications.
	"""

	try:
		_apns_send(
			registration_id, alert, application_id=application_id,
			creds=creds, **kwargs
		)
	except apns2_errors.APNsException as apns2_exception:
		if isinstance(apns2_exception, apns2_errors.Unregistered):
			device = models.APNSDevice.objects.get(registration_id=registration_id)
			device.active = False
			device.save()

		raise APNSServerError(status=apns2_exception.__class__.__name__)


def apns_send_bulk_message(
	registration_ids, alert, application_id=None, creds=None, **kwargs
):
	"""
	Sends an APNS notification to one or more registration_ids.
	The registration_ids argument needs to be a list.

	Note that if set alert should always be a string. If it is not set,
	it won"t be included in the notification. You will need to pass None
	to this for silent notifications.
	"""

	results = _apns_send(
		registration_ids, alert, batch=True, application_id=application_id,
		creds=creds, **kwargs
	)
	inactive_tokens = [token for token, result in results.items() if result == "Unregistered"]
	models.APNSDevice.objects.filter(registration_id__in=inactive_tokens).update(active=False)
	return results
