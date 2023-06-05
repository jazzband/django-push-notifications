"""
Apple Push Notification Service
Documentation is available on the iOS Developer Library:
https://developer.apple.com/library/content/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/APNSOverview.html
"""
import json

import requests

from . import models
from .conf import get_manager
from .exceptions import APNSServerError

DELETE_ERROR_CODES = [
    'DeviceTokenNotForTopic',
    'BadDeviceToken',
    'BadTopic',
    'TopicDisallowed',
    'PayloadEmpty',
    'BadCertificate',
    'BadCertificateEnvironment',
    'Unregistered',
    'PayloadTooLarge'
]


def _apns_send(registration_id, alert, application_id, category=None, content_available=None, badge=None, title=None,
               extra=None, **kwargs):
    notification_type = (extra.get('type') if extra else None) or None
    inner_data = {'json': json.dumps(extra or {})}
    if notification_type:
        inner_data.update(type=notification_type)

    payload = {
        'token': registration_id,
        'topic': get_manager().get_apns_topic(),
        'title': title,
        'body': alert,
        'data': inner_data
    }
    if badge is not None:
        payload['badge'] = badge
    if category is not None:
        payload['category'] = category
    if content_available is not None:
        payload['content-available'] = content_available

    base_url = get_manager().get_post_url('APNS', application_id)
    mode = 'dev' if get_manager().get_apns_use_sandbox(application_id) else 'prod'
    url = f'{base_url}/{mode}/push'
    response = requests.post(url, json=payload)
    if response.status_code != 204:
        text = response.text()
        if any(e for e in DELETE_ERROR_CODES if e in text):
            return False
        raise APNSServerError(status=text)
    return True


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

    if not _apns_send(
            registration_id, alert, application_id=application_id,
            **kwargs
    ):
        device = models.APNSDevice.objects.get(registration_id=registration_id)
        device.active = False
        device.save()


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
    raise NotImplemented()
    # results = _apns_send(
    #     registration_ids, alert, batch=True, application_id=application_id,
    #      **kwargs
    # )
    # inactive_tokens = [token for token, result in results.items() if result == "Unregistered"]
    # models.APNSDevice.objects.filter(registration_id__in=inactive_tokens).update(active=False)
    # return results
