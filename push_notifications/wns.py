"""
Windows Notification Service

Documentation is available on the Windows Dev Center:
https://msdn.microsoft.com/en-us/windows/uwp/controls-and-patterns/
tiles-and-notifications-windows-push-notification-services--wns--overview
"""

import json
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring

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

WNS_ACCESS_URL = "https://login.live.com/accesstoken.srf"


class WNSError(NotificationError):
    pass


def _wns_authenticate():
    """
    Requests an Access token for WNS communication.

    :return: dict: {'access_token': <String>, 'expires_in': <Int>, 'token_type': 'bearer'}
    """
    package_id = SETTINGS.get("WNS_PACKAGE_SECURITY_ID")
    secret_key = SETTINGS.get("WNS_SECRET_KEY")
    if not package_id:
        raise ImproperlyConfigured(
            'You need to set PUSH_NOTIFICATIONS_SETTINGS["WNS_PACKAGE_SECURITY_ID"] to send messages through WNS.')
    if not secret_key:
        raise ImproperlyConfigured(
            'You need to set PUSH_NOTIFICATIONS_SETTINGS["WNS_SECRET_KEY"] to send messages through WNS.')

    data = "grant_type=client_credentials&client_id=%(client_id)s&client_secret=%(client_secret)s" \
           "&scope=notify.windows.com" % {"client_id": package_id, "client_secret": secret_key}
    data_bytes = bytes(data, "utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    request = Request(WNS_ACCESS_URL, data=data_bytes, headers=headers)
    return json.loads(urlopen(request).read().decode("utf-8"))


def _wns_send(uri, data, wns_type="wns/raw"):
    """
    Sends a notification data and authentication to WNS.

    :param uri: String: The device's unique notification URI
    :param data: dict: The notification data to be sent.
    :return:
    """
    access_token = _wns_authenticate()["access_token"]

    authorization = "Bearer %(token)s" % {"token": access_token}

    content_type = "application/octet-stream"
    if wns_type != "wns_raw":
        content_type = "text/xml"

    headers = {
        "Content-Type": content_type,  # "text/xml" (toast/badge/tile) | "application/octet-stream" (raw)
        "Authorization": authorization,
        "Content-Length": str(len(data)),
        "X-WNS-Type": wns_type,  # wns/toast | wns/badge | wns/tile | wns/raw
    }

    request = Request(uri, data, headers)
    return urlopen(request).read().decode("utf-8")


def _wns_prepare_toast(data):
    """
    Creates the xml tree for a 'toast' notification

    :param data: dict: The notification data to be converted to an xml tree.
    :return: String
    """
    root = ET.Element("toast")
    visual = ET.SubElement(root, "visual")
    binding = ET.SubElement(visual, "binding")
    if "text" in data:
        for count, item in enumerate(data["text"]):
            elem = ET.SubElement(binding, "text")
            elem.text = item
            elem.attrib["id"] = str(count)
    if "image" in data:
        for count, item in enumerate(data["image"]):
            elem = ET.SubElement(binding, "img")
            elem.attrib["src"] = item
            elem.attrib["id"] = str(count)
    return tostring(root, encoding='utf-8')


def _wns_prepare_tile(data):
    """
    Creates the xml tree for a 'tile' notification

    :param data: dict: The notification data to be converted to an xml tree.
    :return: String
    """
    root = ET.Element("tile")
    visual = ET.SubElement(root, "visual")
    binding = ET.SubElement(visual, "binding")
    if "text" in data:
        for count, item in enumerate(data["text"]):
            elem = ET.SubElement(binding, "text")
            elem.text = item
            elem.attrib["id"] = str(count)
    if "image" in data:
        for count, item in enumerate(data["image"]):
            elem = ET.SubElement(binding, "img")
            elem.attrib["src"] = item
            elem.attrib["id"] = str(count)
    return tostring(root, encoding='utf-8')


def _wns_prepare_badge(data):
    """
    Creates the xml tree for a 'badge' notification

    :param data: dict: The notification data to be converted to an xml tree.
    :return: String
    """
    root = ET.Element("badge")
    root.attrib["value"] = data["value"]
    return tostring(root, encoding='utf-8')


def _wns_prepare_raw(data):
    """
    There is nothing that needs to be done to raw notification data(hence, the name), this is mostly a placeholder.

    :param data: Notification data
    :return:
    """
    return data


def wns_send_message(uri, notification_type, data):
    """
    Sends a notification request to WNS. The data will be converted to the correct format per notification_type.

    :param uri: String: The device's unique notification uri.
    :param notification_type: String: The type of windows notification to be sent. [toast | badge | tile | raw]
    :param data: String: The notification data to be sent.
    """
    types = {
        "badge": _wns_prepare_badge,
        "toast": _wns_prepare_toast,
        "tile": _wns_prepare_tile,
        "raw": _wns_prepare_raw,
    }

    wns_type = 'wns/' + notification_type
    prepared_data = types[notification_type](data=data)

    _wns_send(uri=uri, data=prepared_data, wns_type=wns_type)


def wns_send_bulk_message(uri_list, data, **kwargs):
    """
    WNS doesn't support bulk notification, so we loop through each uri.

    :param uri_list: list: A list of each device's unique notification uri.
    :param data: dict: The notification data to be sent.
    :param kwargs:
    """
    if uri_list:
        notification_type = kwargs.pop('notification_type', 'raw')
        for uri in uri_list:
            wns_send_message(uri=uri, notification_type=notification_type, data=data)
