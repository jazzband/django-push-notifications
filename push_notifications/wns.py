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
	from urllib.error import HTTPError
	from urllib.request import Request, urlopen
	from urllib.parse import urlencode
except ImportError:
	# Python 2 support
	from urllib2.error import HTTPError
	from urllib2 import Request, urlopen
	from urllib import urlencode

from django.core.exceptions import ImproperlyConfigured

from . import NotificationError
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS

WNS_ACCESS_URL = "https://login.live.com/accesstoken.srf"


class WNSError(NotificationError):
	pass


class WNSAuthenticationError(WNSError):
	pass


class WNSNotificationResponseError(WNSError):
	pass


def _wns_authenticate():
	"""
	Requests an Access token for WNS communication.

	:return: dict: {'access_token': <str>, 'expires_in': <int>, 'token_type': 'bearer'}
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
	try:
		response = urlopen(request)
	except HTTPError as err:
		if err.code == 400:
			# One of your settings is probably jacked up.
			# https://msdn.microsoft.com/en-us/library/windows/apps/xaml/hh868245
			raise WNSAuthenticationError("Authentication failed, check your WNS settings.")
		raise err
	return json.loads(response.read().decode("utf-8"))


def _wns_send(uri, data, wns_type="wns/toast"):
	"""
	Sends a notification data and authentication to WNS.

	:param uri: str: The device's unique notification URI
	:param data: dict: The notification data to be sent.
	:return:
	"""
	access_token = _wns_authenticate()["access_token"]

	authorization = "Bearer %(token)s" % {"token": access_token}

	content_type = "text/xml"
	if wns_type == "wns/raw":
		content_type = "application/octet-stream"

	headers = {
		"Content-Type": content_type,  # "text/xml" (toast/badge/tile) | "application/octet-stream" (raw)
		"Authorization": authorization,
		"X-WNS-Type": wns_type,  # wns/toast | wns/badge | wns/tile | wns/raw
	}

	if type(data) is str:
		data = data.encode('utf-8')

	request = Request(uri, data, headers)

	# A lot of things can happen, let 'em know which one.
	try:
		response = urlopen(request)
	except HTTPError as err:
		if err.code == 400:
			raise WNSNotificationResponseError("HTTP 400: One or more headers were specified incorrectly or conflict "
											   "with another header.")
		elif err.code == 401:
			raise WNSNotificationResponseError("HTTP 401: The cloud service did not present a valid authentication "
											   "ticket. Access token may be invalid.")
		elif err.code == 403:
			raise WNSNotificationResponseError("HTTP 403: The cloud service is not authorized to send a notification to"
											   " this URI even though they are authenticated.")
		elif err.code == 404:
			raise WNSNotificationResponseError("HTTP 404: The channel URI is not valid or is not recognized by WNS.")
		elif err.code == 405:
			raise WNSNotificationResponseError("HTTP 405: Invalid method (GET, CREATE); only POST (Windows or Windows "
											   "Phone) or DELETE (Windows Phone only) is allowed.")
		elif err.code == 406:
			raise WNSNotificationResponseError("HTTP 406: The cloud service exceeded its throttle limit.")
		elif err.code == 410:
			raise WNSNotificationResponseError("HTTP 410: The channel expired.")
		elif err.code == 413:
			raise WNSNotificationResponseError("HTTP 413: The notification payload exceeds the 5000 byte size limit.")
		elif err.code == 500:
			raise WNSNotificationResponseError("HTTP 500: An internal failure caused notification delivery to fail.")
		elif err.code == 503:
			raise WNSNotificationResponseError("HTTP 503: The server is currently unavailable.")
		raise err

	return response.read().decode("utf-8")


def _wns_prepare_toast(data, **kwargs):
	"""
	Creates the xml tree for a 'toast' notification

	:param data: dict: The notification data to be converted to an xml tree.

	{
		'text': ['Title text', 'Message Text', 'Another message!'],
		'image': ['src1', 'src2'],
	}

	:return: str
	"""
	root = ET.Element("toast")
	visual = ET.SubElement(root, "visual")
	binding = ET.SubElement(visual, "binding")
	binding.attrib["template"] = kwargs.pop("template", "ToastText01")
	if "text" in data:
		for count, item in enumerate(data["text"], start=1):
			elem = ET.SubElement(binding, "text")
			elem.text = item
			elem.attrib["id"] = str(count)
	if "image" in data:
		for count, item in enumerate(data["image"], start=1):
			elem = ET.SubElement(binding, "img")
			elem.attrib["src"] = item
			elem.attrib["id"] = str(count)
	return tostring(root)


def wns_send_message(uri, message=None, xml_data=None, raw_data=None, **kwargs):
	"""
	Sends a notification request to WNS. There are four notification types that WNS can send: toast, tile, badge,
	and raw. Toast, tile, and badge can all be customized to use different templates/icons/sounds/launch params/etc.
	See docs for more information:
	https://msdn.microsoft.com/en-us/library/windows/apps/br212853.aspx

	There are three ways to input notification data:

	1. The simplest and least custom notification to send is to just pass a string to message. This will create a toast
	notification with one text element.
		e.g.:
			"This is my notification title"

	2. Passing a dictionary to xml_data will create one of three types of notifications depending on the
	dictionary data (toast, tile, badge).
		See 'dict_to_xml_schema' docs for more information on dictionary formatting.

	3. Passing a value to raw_data will create a 'raw' notification and send the input data as is.

	:param uri: str: The device's unique notification uri.
	:param message: str: The notification data to be sent.
	:param xml_data: dict: A dictionary containing data to be converted to an xml tree.
	:param raw_data: str: Data to be sent via a 'raw' notification.
	"""
	# Create a simple toast notification
	if message:
		wns_type = "wns/toast"
		data = {
			"text": [message, ],
		}
		prepared_data = _wns_prepare_toast(data=data, **kwargs)
	# Create a toast/tile/badge notification from a dictionary
	elif xml_data:
		xml = dict_to_xml_schema(xml_data)
		wns_type = "wns/%s" % xml.tag
		prepared_data = tostring(xml)
	# Create a raw notification
	elif raw_data:
		wns_type = "wns/raw"
		prepared_data = raw_data
	else:
		raise TypeError("At least one of the following parameters cannot be None type: "
						"['message', 'xml_data', 'raw_data']")

	_wns_send(uri=uri, data=prepared_data, wns_type=wns_type)


def wns_send_bulk_message(uri_list, message=None, xml_data=None, raw_data=None, **kwargs):
	"""
	WNS doesn't support bulk notification, so we loop through each uri.

	:param uri_list: list: A list of uris the notification will be sent to.
	:param message: str: The notification data to be sent.
	:param xml_data: dict: A dictionary containing data to be converted to an xml tree.
	:param raw_data: str: Data to be sent via a 'raw' notification.
	"""
	if uri_list:
		for uri in uri_list:
			wns_send_message(uri=uri, message=message, xml_data=xml_data, raw_data=raw_data, **kwargs)


def dict_to_xml_schema(data):
	"""
	Input a dictionary to be converted to xml. There should be only one key at the top level. The value must be a dict
	with (required)'children' key and (optional)'attrs' key. This will be called the 'sub-element dictionary'.

	The 'attrs' value must be a dictionary; each value will be added to the element's xml tag as attributes:

		e.g.:
			{
				'example': {
					'attrs': {
						'key1': 'value1',
						...
					},
					...
				}
			}

		would result in:
			<example key1="value1" key2="value2"></example>

	The 'children' key is required.
	If the value is a dict it must contain one or more keys which will be used as the sub-element names. Each
	sub-element must have a value of a sub-element dictionary(see above) or a list of sub-element dictionaries.
	If the value is not a dict, it will be the value of the element.
	If the value is a list, multiple elements of the same tag will be created from each sub-element dict in the list.

	:param data: dict: Used to create an XML tree.
		e.g.:
			example_data = {
				'toast': {
					'attrs': {
						'launch': 'param',
						'duration': 'short',
					},
					'children': {
						'visual': {
							'children': {
								'binding': {
									'attrs': {
										'template': 'ToastText01',
									},
									'children': {
										'text': [
											{
												'attrs': {
													'id': '1',
												},
												'children': 'text1',
											},
											{
												'attrs': {
													'id': '2',
												},
												'children': 'text2',
											},
										],
									},
								},
							},
						},
					},
				},
			}
	:return: ElementTree.Element
	"""
	for key, value in data.items():
		root = _add_element_attrs(ET.Element(key), value.get('attrs', {}))
		children = value.get('children', None)
		if isinstance(children, dict):
			_add_sub_elements_from_dict(root, children)
		return root


def _add_sub_elements_from_dict(parent, sub_dict):
	"""
	Add SubElements to the parent element.

	:param parent: ElementTree.Element: The element the newly created SubElement will be added to.
	:param sub_dict: dict: Used to create a new SubElement.
		See the 'dict_to_xml_schema' method docstring for more information.
			e.g.:
				{
					'example': {
						'attrs': {
							'key1': 'value1',
							...
						},
						...
					}
				}
	"""
	for key, value in sub_dict.items():
		if isinstance(value, list):
			for repeated_element in value:
				sub_element = ET.SubElement(parent, key)
				_add_element_attrs(sub_element, repeated_element.get('attrs', {}))
				children = repeated_element.get('children', None)
				if isinstance(children, dict):
					_add_sub_elements_from_dict(sub_element, children)
				elif isinstance(children, str):
					sub_element.text = children
		else:
			sub_element = ET.SubElement(parent, key)
			_add_element_attrs(sub_element, value.get('attrs', {}))
			children = value.get('children', None)
			if isinstance(children, dict):
				_add_sub_elements_from_dict(sub_element, children)
			elif isinstance(children, str):
				sub_element.text = children


def _add_element_attrs(elem, attrs):
	"""
	Add attributes to the given element.

	:param elem: ElementTree.Element: The element the attributes are being added to.
	:param attrs: dict: A dictionary of attributes.
		e.g.:
			{'attribute1': 'value', 'attribute2': 'another'}
	:return: ElementTree.Element
	"""
	for attr, value in attrs.items():
		elem.attrib[attr] = value
	return elem
