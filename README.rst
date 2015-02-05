django-push-notifications
=========================

.. image:: https://api.travis-ci.org/jleclanche/django-push-notifications.png
	:target: https://travis-ci.org/jleclanche/django-push-notifications

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

Tastypie support should work on Tastypie 0.9.11 and newer.

Django versions older than 1.5 require 'six' to be installed.
Django versions older than 1.7 require 'south' to be installed.
Django versions older than 1.8 require 'django-uuidfield' to be installed.


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

Note: If you are planning on running your project with `DEBUG=True`, then make sure you have set the
*development* certificate as your `APNS_CERTIFICATE`. Otherwise the app will not be able to connect to the correct host.

You can learn more about APNS certificates here: https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/ProvisioningDevelopment.html

Native Django migrations are supported on Django 1.7 and beyond. The app will automatically
fall back to South on older versions, however you will also need the following setting::

	SOUTH_MIGRATION_MODULES = {"push_notifications": "push_notifications.south_migrations"}


Settings list
-------------
All settings are contained in a PUSH_NOTIFICATIONS_SETTINGS dict.

In order to use GCM, you are required to include GCM_API_KEY.
For APNS, you are required to include APNS_CERTIFICATE.

- APNS_CERTIFICATE: Absolute path to your APNS certificate file. Certificates with passphrases are not supported.
- GCM_API_KEY: Your API key for GCM.
- APNS_HOST: The hostname used for the APNS sockets. When DEBUG=True, this defaults to gateway.sandbox.push.apple.com. When DEBUG=False, this defaults to gateway.push.apple.com.
- APNS_PORT: The port used along with APNS_HOST. Defaults to 2195.
- GCM_POST_URL: The full url that GCM notifications will be POSTed to. Defaults to https://android.googleapis.com/gcm/send.
- GCM_MAX_RECIPIENTS: The maximum amount of recipients that can be contained per bulk message. If the registration_ids list is larger than that number, multiple bulk messages will be sent. Defaults to 1000 (the maximum amount supported by GCM).

Sending messages
----------------
GCM and APNS services have slightly different semantics. The app tries to offer a common interface for both when using the models.

::

	from push_notifications.models import APNSDevice, GCMDevice

	device = GCMDevice.objects.get(registration_id=gcm_reg_id)
	# The first argument will be sent as "message" to the intent extras Bundle
	# Retrieve it with intent.getExtras().getString("message")
	device.send_message("You've got mail")
	# If you want to customize, send an extra dict and a None message.
	# the extras dict will be mapped into the intent extras Bundle.
	# For dicts where all values are keys this will be sent as url parameters,
	# but for more complex nested collections the extras dict will be sent via
	# the bulk message api.
	device.send_message(None, extra={"foo": "bar"})

	device = APNSDevice.objects.get(registration_id=apns_token)
	device.send_message("You've got mail") # Alert message may only be sent as text.
	device.send_message(None, badge=5) # No alerts but with badge.
	device.send_message(None, badge=1, extra={"foo": "bar"}) # Silent message with badge and added custom data.

Note that APNS does not support sending payloads that exceed 2048 bytes (increased from 256 in 2014).
The message is only one part of the payload, if
once constructed the payload exceeds the maximum size, an APNSDataOverflow exception will be raised before anything is sent.


Sending messages in bulk
------------------------
::

	from push_notifications.models import APNSDevice, GCMDevice

	devices = GCMDevice.objects.filter(user__first_name="James")
	devices.send_message("Happy name day!")

Sending messages in bulk makes use of the bulk mechanics offered by GCM and APNS. It is almost always preferable to send
bulk notifications instead of single ones.

Administration
--------------
APNS devices which are not receiving push notifications can be set to inactive by two methods.  The web admin interface for
APNS devices has a "prune devices" option.  Any selected devices which are not receiving notifications will be set to inactive(*).
There is also a management command to prune all devices failing to receive notifications::

	python manage.py prune_devices

This removes all devices which are not receiving notifications.

For more information, please refer to the APNS feedback service_.

.. _service: https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/CommunicatingWIthAPS.html

(*)Any devices which are not selected, but are not receiving notifications will not be deactivated on a subsequent call to "prune devices" unless another
attempt to send a message to the device fails after the call to the feedback service.

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

django-push-notifications is compatible with Python 3. Django 1.8 or higher is recommended.
