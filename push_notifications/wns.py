"""
Windows Notification Service

Documentation is available on the Windows Dev Center:
https://msdn.microsoft.com/en-us/windows/uwp/controls-and-patterns/tiles-and-notifications-windows-push-notification-services--wns--overview
"""

import json
import xml.etree.ElementTree as ET

from django.core.exceptions import ImproperlyConfigured

from .compat import HTTPError, Request, urlencode, urlopen
from .conf import get_manager
from .exceptions import NotificationError
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


class WNSError(NotificationError):
	pass


class WNSAuthenticationError(WNSError):
	pass


class WNSNotificationResponseError(WNSError):
	pass


def _wns_authenticate(scope="notify.windows.com", application_id=None):
	"""
	Requests an Access token for WNS communication.

	:return: dict: {'access_token': <str>, 'expires_in': <int>, 'token_type': 'bearer'}
	"""
	client_id = get_manager().get_wns_package_security_id(application_id)
	client_secret = get_manager().get_wns_secret_key(application_id)
	if not client_id:
		raise ImproperlyConfigured(
			'You need to set PUSH_NOTIFICATIONS_SETTINGS["WNS_PACKAGE_SECURITY_ID"] to use WNS.'
		)

	if not client_secret:
		raise ImproperlyConfigured(
			'You need to set PUSH_NOTIFICATIONS_SETTINGS["WNS_SECRET_KEY"] to use WNS.'
		)

	headers = {
		"Content-Type": "application/x-www-form-urlencoded",
	}
	params = {
		"grant_type": "client_credentials",
		"client_id": client_id,
		"client_secret": client_secret,
		"scope": scope,
	}
	data = urlencode(params).encode("utf-8")

	request = Request(SETTINGS["WNS_ACCESS_URL"], data=data, headers=headers)
	try:
		response = urlopen(request)
	except HTTPError as err:
		if err.code == 400:
			# One of your settings is probably jacked up.
			# https://msdn.microsoft.com/en-us/library/windows/apps/xaml/hh868245
			raise WNSAuthenticationError("Authentication failed, check your WNS settings.")
		raise err

	oauth_data = response.read().decode("utf-8")
	try:
		oauth_data = json.loads(oauth_data)
	except Exception:
		# Upstream WNS issue
		raise WNSAuthenticationError("Received invalid JSON data from WNS.")

	access_token = oauth_data.get("access_token")
	if not access_token:
		# Upstream WNS issue
		raise WNSAuthenticationError("Access token missing from WNS response.")

	return access_token


def _wns_send(uri, data, wns_type="wns/toast", application_id=None):
	"""
	Sends a notification data and authentication to WNS.

	:param uri: str: The device's unique notification URI
	:param data: dict: The notification data to be sent.
	:return:
	"""
	access_token = _wns_authenticate(application_id=application_id)

	content_type = "text/xml"
	if wns_type == "wns/raw":
		content_type = "application/octet-stream"

	headers = {
		# content_type is "text/xml" (toast/badge/tile) | "application/octet-stream" (raw)
		"Content-Type": content_type,
		"Authorization": "Bearer %s" % (access_token),
		"X-WNS-Type": wns_type,  # wns/toast | wns/badge | wns/tile | wns/raw
	}

	if type(data) is str:
		data = data.encode("utf-8")

	request = Request(uri, data, headers)

	# A lot of things can happen, let them know which one.
	try:
		response = urlopen(request)
	except HTTPError as err:
		if err.code == 400:
			msg = "One or more headers were specified incorrectly or conflict with another header."
		elif err.code == 401:
			msg = "The cloud service did not present a valid authentication ticket."
		elif err.code == 403:
			msg = "The cloud service is not authorized to send a notification to this URI."
		elif err.code == 404:
			msg = "The channel URI is not valid or is not recognized by WNS."
		elif err.code == 405:
			msg = "Invalid method. Only POST or DELETE is allowed."
		elif err.code == 406:
			msg = "The cloud service exceeded its throttle limit"
		elif err.code == 410:
			msg = "The channel expired."
		elif err.code == 413:
			msg = "The notification payload exceeds the 500 byte limit."
		elif err.code == 500:
			msg = "An internal failure caused notification delivery to fail."
		elif err.code == 503:
			msg = "The server is currently unavailable."
		else:
			raise err
		raise WNSNotificationResponseError("HTTP %i: %s" % (err.code, msg))

	return response.read().decode("utf-8")


def _wns_prepare_toast(data, **kwargs):
	"""
	Creates the xml tree for a `toast` notification

	:param data: dict: The notification data to be converted to an xml tree.

	{
		"text": ["Title text", "Message Text", "Another message!"],
		"image": ["src1", "src2"],
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
	return ET.tostring(root)


def wns_send_message(
	uri, message=None, xml_data=None, raw_data=None, application_id=None, **kwargs
):
	"""
	Sends a notification request to WNS.
	There are four notification types that WNS can send: toast, tile, badge and raw.
	Toast, tile, and badge can all be customized to use different
	templates/icons/sounds/launch params/etc.
	See docs for more information:
	https://msdn.microsoft.com/en-us/library/windows/apps/br212853.aspx

	There are multiple ways to input notification data:

	1. The simplest and least custom notification to send is to just pass a string
	to `message`. This will create a toast notification with one text element. e.g.:
		"This is my notification title"

	2. You can also pass a dictionary to `message`: it can only contain one or both
	keys: ["text", "image"]. The value of each key must be a list with the text and
	src respectively. e.g.:
		{
			"text": ["text1", "text2"],
			"image": ["src1", "src2"],
		}

	3. Passing a dictionary to `xml_data` will create one of three types of
	notifications depending on the dictionary data (toast, tile, badge).
	See `dict_to_xml_schema` docs for more information on dictionary formatting.

	4. Passing a value to `raw_data` will create a `raw` notification and send the
	input data as is.

	:param uri: str: The device's unique notification uri.
	:param message: str|dict: The notification data to be sent.
	:param xml_data: dict: A dictionary containing data to be converted to an xml tree.
	:param raw_data: str: Data to be sent via a `raw` notification.
	"""
	# Create a simple toast notification
	if message:
		wns_type = "wns/toast"
		if isinstance(message, str):
			message = {
				"text": [message, ],
			}
		prepared_data = _wns_prepare_toast(data=message, **kwargs)
	# Create a toast/tile/badge notification from a dictionary
	elif xml_data:
		xml = dict_to_xml_schema(xml_data)
		wns_type = "wns/%s" % xml.tag
		prepared_data = ET.tostring(xml)
	# Create a raw notification
	elif raw_data:
		wns_type = "wns/raw"
		prepared_data = raw_data
	else:
		raise TypeError(
			"At least one of the following parameters must be set:"
			"`message`, `xml_data`, `raw_data`"
		)

	return _wns_send(
		uri=uri, data=prepared_data, wns_type=wns_type, application_id=application_id
	)


def wns_send_bulk_message(
	uri_list, message=None, xml_data=None, raw_data=None, application_id=None, **kwargs
):
	"""
	WNS doesn't support bulk notification, so we loop through each uri.

	:param uri_list: list: A list of uris the notification will be sent to.
	:param message: str: The notification data to be sent.
	:param xml_data: dict: A dictionary containing data to be converted to an xml tree.
	:param raw_data: str: Data to be sent via a `raw` notification.
	"""
	res = []
	if uri_list:
		for uri in uri_list:
			r = wns_send_message(
				uri=uri, message=message, xml_data=xml_data,
				raw_data=raw_data, application_id=application_id, **kwargs
			)
			res.append(r)
	return res


def dict_to_xml_schema(data):
	"""
	Input a dictionary to be converted to xml. There should be only one key at
	the top level. The value must be a dict with (required) `children` key and
	(optional) `attrs` key. This will be called the `sub-element dictionary`.

	The `attrs` value must be a dictionary; each value will be added to the
	element's xml tag as attributes. e.g.:
		{"example": {
			"attrs": {
				"key1": "value1",
				...
			},
			...
		}}

	would result in:
		<example key1="value1" key2="value2"></example>

	If the value is a dict it must contain one or more keys which will be used
	as the sub-element names. Each sub-element must have a value of a sub-element
	dictionary(see above) or a list of sub-element dictionaries.
	If the value is not a dict, it will be the value of the element.
	If the value is a list, multiple elements of the same tag will be created
	from each sub-element dict in the list.

	:param data: dict: Used to create an XML tree. e.g.:
		example_data = {
			"toast": {
				"attrs": {
					"launch": "param",
					"duration": "short",
				},
				"children": {
					"visual": {
						"children": {
							"binding": {
								"attrs": {"template": "ToastText01"},
								"children": {
									"text": [
										{
											"attrs": {"id": "1"},
											"children": "text1",
										},
										{
											"attrs": {"id": "2"},
											"children": "text2",
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
		root = _add_element_attrs(ET.Element(key), value.get("attrs", {}))
		children = value.get("children", None)
		if isinstance(children, dict):
			_add_sub_elements_from_dict(root, children)
		return root


def _add_sub_elements_from_dict(parent, sub_dict):
	"""
	Add SubElements to the parent element.

	:param parent: ElementTree.Element: The parent element for the newly created SubElement.
	:param sub_dict: dict: Used to create a new SubElement. See `dict_to_xml_schema`
	method docstring for more information. e.g.:
		{"example": {
			"attrs": {
				"key1": "value1",
				...
			},
			...
		}}
	"""
	for key, value in sub_dict.items():
		if isinstance(value, list):
			for repeated_element in value:
				sub_element = ET.SubElement(parent, key)
				_add_element_attrs(sub_element, repeated_element.get("attrs", {}))
				children = repeated_element.get("children", None)
				if isinstance(children, dict):
					_add_sub_elements_from_dict(sub_element, children)
				elif isinstance(children, str):
					sub_element.text = children
		else:
			sub_element = ET.SubElement(parent, key)
			_add_element_attrs(sub_element, value.get("attrs", {}))
			children = value.get("children", None)
			if isinstance(children, dict):
				_add_sub_elements_from_dict(sub_element, children)
			elif isinstance(children, str):
				sub_element.text = children


def _add_element_attrs(elem, attrs):
	"""
	Add attributes to the given element.

	:param elem: ElementTree.Element: The element the attributes are being added to.
	:param attrs: dict: A dictionary of attributes. e.g.:
		{"attribute1": "value", "attribute2": "another"}
	:return: ElementTree.Element
	"""
	for attr, value in attrs.items():
		elem.attrib[attr] = value
	return elem
