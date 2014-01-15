django-push-notifications
=========================

.. image:: https://api.travis-ci.org/Adys/django-push-notifications.png
	:target: https://travis-ci.org/Adys/django-push-notifications

A minimal Django app that implements Device models that can send messages through APNS and GCM.

The app implements two models: GCMDevice and APNSDevice. Those models share the same attributes:
 - name (optional): A name for the device.
 - is_active (default True): A boolean that determines whether the device will be sent notifications.
 - user (optional): A foreign key to auth.User, if you wish to link the device to a specific user.
 - device_id (optional): A UUID for the device obtained from Android/iOS APIs, if you wish to uniquely identify it.
 - registration_id (required): The GCM registration id or the APNS token for the device.


The app also implements an admin panel, through which you can test single and bulk notifications. Select one or more
GCM or APNS devices and in the action dropdown, select "Send test message" or "Send test message in bulk", accordingly.
Note that sending a non-bulk test message to more than one device will just iterate over the devices and send multiple
single messages.


Dependencies
------------
All versions of Django 1.0 and newer should be supported, however no guarantees are made for versions older than 1.4.
The app also depends on django-uuidfield.

Tastypie support should work on Tastypie 0.9.11 and newer.

Django versions older than 1.5 require 'six' to be installed.


Setup
-----
You can install the library directly from pypi using pip::

	$ pip install django-push-notifications


Edit your settings.py file::

	INSTALLED_APPS = (
		...
		"push_notifications"
	)

	PUSH_NOTIFICATIONS_SETTINGS = {
		"GCM_API_KEY": "<your api key>",
		"APNS_CERTIFICATE": "/path/to/your/certificate.pem",
	}


Settings list
-------------
All settings are contained in a PUSH_NOTIFICATIONS_SETTINGS dict.

In order to use GCM, you are required to include GCM_API_KEY.
For APNS, you are required to include APNS_CERTIFICATE.

 - APNS_CERTIFICATE: Absolute path to your APNS certificate file. Certificates with passphrases are not supported.
 - GCM_API_KEY: Your API key for GCM.
 - APNS_HOST: The hostname used for the APNS sockets. When DEBUG=True, this defaults to gateway.sandbox.push.apple.com.
   When DEBUG=False, this defaults to gateway.push.apple.com.
 - APNS_PORT: The port used along with APNS_HOST. Defaults to 2195.
 - GCM_POST_URL: The full url that GCM notifications will be POSTed to. Defaults to https://android.googleapis.com/gcm/send.
 - GCM_MAX_RECIPIENTS: The maximum amount of recipients that can be contained per bulk message. If the registration_ids list
   is larger than that number, multiple bulk messages will be sent. Defaults to 1000 (the maximum amount supported by GCM).

Sending messages
----------------
::

	from push_notifications.models import APNSDevice, GCMDevice

	device = GCMDevice.objects.get(registration_id=gcm_reg_id)
	device.send_message({"foo": "bar"}) # The message will be sent and received as json.

	device = APNSDevice.objects.get(registration_id=apns_token)
	device.send_message("You've got mail") # The message may only be sent as text.

Note that APNS does not support sending payloads that exceed 256 bytes. The message is only one part of the payload, if
once constructed the payload exceeds the maximum size, an APNSDataOverflow exception will be raised before anything is sent.


Sending messages in bulk
------------------------
::

	from push_notifications.models import APNSDevice, GCMDevice

	devices = GCMDevice.objects.filter(user__first_name="James")
	devices.send_message({"message": "Happy name day!"})

Sending messages in bulk makes use of the bulk mechanics offered by GCM and APNS. It is almost always preferable to send
bulk notifications instead of single ones.
Note that in GCM, the device will receive data in a different format depending on whether it's been sent in bulk or not.


Exceptions
----------

 - NotificationError(Exception): Base exception for all notification-related errors.
 - gcm.GCMError(NotificationError): An error was returned by GCM. This is never raised when using bulk notifications.
 - apns.APNSError(NotificationError): Something went wrong upon sending APNS notifications.
 - apns.APNSDataOverflow(APNSError): The APNS payload exceeds its maximum size and cannot be sent.


Tastypie support
----------------

The app includes tastypie-compatible resources in push_notifications.api. These can be used as-is, or as base classes
for more involved APIs.
The following resources are available:
 - APNSDeviceResource
 - GCMDeviceResource
 - APNSDeviceAuthenticatedResource
 - GCMDeviceAuthenticatedResource

The base device resources will not ask for authentication, while the authenticated ones will link the logged in user to
the device they register.
Subclassing the authenticated resources in order to add a SameUserAuthentication and a user ForeignKey is recommended.

When registered, the APIs will show up at <api_root>/device/apns and <api_root>/device/gcm, respectively.


Python 3 support
----------------

django-push-notifications has been tested on Python 3 and should work. However, the django-uuidfield dependency does not
officially support Python 3. A pull request is pending and can be used for the time being::

	pip install -e git://github.com/dominicrodger/django-uuidfield.git@python3#egg=django_uuidfield
