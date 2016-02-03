django-push-notifications
=========================
.. image:: https://api.travis-ci.org/jleclanche/django-push-notifications.png
	:target: https://travis-ci.org/jleclanche/django-push-notifications

A minimal Django app that implements Device models that can send messages through APNS and GCM.

The app implements two models: ``GCMDevice`` and ``APNSDevice``. Those models share the same attributes:
 - ``name`` (optional): A name for the device.
 - ``active`` (default True): A boolean that determines whether the device will be sent notifications.
 - ``user`` (optional): A foreign key to auth.User, if you wish to link the device to a specific user.
 - ``device_id`` (optional): A UUID for the device obtained from Android/iOS APIs, if you wish to uniquely identify it.
 - ``registration_id`` (required): The GCM registration id or the APNS token for the device.


The app also implements an admin panel, through which you can test single and bulk notifications. Select one or more
GCM or APNS devices and in the action dropdown, select "Send test message" or "Send test message in bulk", accordingly.
Note that sending a non-bulk test message to more than one device will just iterate over the devices and send multiple
single messages.

Dependencies
------------
Django 1.8 is required. Support for older versions is available in the release 1.2.1.

Tastypie support should work on Tastypie 0.11.0 and newer.

Django REST Framework support should work on DRF version 3.0 and newer.

Setup
-----
You can install the library directly from pypi using pip:

.. code-block:: shell

	$ pip install django-push-notifications


Edit your settings.py file:

.. code-block:: python

	INSTALLED_APPS = (
		...
		"push_notifications"
	)

	PUSH_NOTIFICATIONS_SETTINGS = {
		"GCM_API_KEY": "[your api key]",
		"APNS_CERTIFICATE": "/path/to/your/certificate.pem",
	}

.. note::
	If you are planning on running your project with ``DEBUG=True``, then make sure you have set the
	*development* certificate as your ``APNS_CERTIFICATE``. Otherwise the app will not be able to connect to the correct host. See settings_ for details.

You can learn more about APNS certificates `here <https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/ProvisioningDevelopment.html>`_.

Native Django migrations are in use. ``manage.py migrate`` will install and migrate all models.

.. _settings:

Settings list
-------------
All settings are contained in a ``PUSH_NOTIFICATIONS_SETTINGS`` dict.

In order to use GCM, you are required to include ``GCM_API_KEY``.
For APNS, you are required to include ``APNS_CERTIFICATE``.

- ``APNS_CERTIFICATE``: Absolute path to your APNS certificate file. Certificates with passphrases are not supported.
- ``APNS_CA_CERTIFICATES``: Absolute path to a CA certificates file for APNS. Optional - do not set if not needed. Defaults to None.
- ``GCM_API_KEY``: Your API key for GCM.
- ``APNS_HOST``: The hostname used for the APNS sockets.
   - When ``DEBUG=True``, this defaults to ``gateway.sandbox.push.apple.com``.
   - When ``DEBUG=False``, this defaults to ``gateway.push.apple.com``.
- ``APNS_PORT``: The port used along with APNS_HOST. Defaults to 2195.
- ``GCM_POST_URL``: The full url that GCM notifications will be POSTed to. Defaults to https://android.googleapis.com/gcm/send.
- ``GCM_MAX_RECIPIENTS``: The maximum amount of recipients that can be contained per bulk message. If the ``registration_ids`` list is larger than that number, multiple bulk messages will be sent. Defaults to 1000 (the maximum amount supported by GCM).
- ``USER_MODEL``: Your user model of choice. Eg. ``myapp.User``. Defaults to ``settings.AUTH_USER_MODEL``.

Sending messages
----------------
GCM and APNS services have slightly different semantics. The app tries to offer a common interface for both when using the models.

.. code-block:: python

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

.. note::
	APNS does not support sending payloads that exceed 2048 bytes (increased from 256 in 2014).
	The message is only one part of the payload, if
	once constructed the payload exceeds the maximum size, an ``APNSDataOverflow`` exception will be raised before anything is sent.

Sending messages in bulk
------------------------
.. code-block:: python

	from push_notifications.models import APNSDevice, GCMDevice

	devices = GCMDevice.objects.filter(user__first_name="James")
	devices.send_message("Happy name day!")

Sending messages in bulk makes use of the bulk mechanics offered by GCM and APNS. It is almost always preferable to send
bulk notifications instead of single ones.


Sending messages to topic members
---------------------------------
GCM topic messaging allows your app server to send a message to multiple devices that have opted in to a particular topic. Based on the publish/subscribe model, topic messaging supports unlimited subscriptions per app. Developers can choose any topic name that matches the regular expression, "/topics/[a-zA-Z0-9-_.~%]+".

.. code-block:: python

	from push_notifications.gcm import gcm_send_message
        
        # First param is "None" because no Registration_id is needed, the message will be sent to all devices subscribed to the topic.
        gcm_send_message(None, "Hello members of my_topic!", topic='/topics/my_topic')

Reference: `GCM Documentation <https://developers.google.com/cloud-messaging/topic-messaging>`_

Administration
--------------

APNS devices which are not receiving push notifications can be set to inactive by two methods.  The web admin interface for
APNS devices has a "prune devices" option.  Any selected devices which are not receiving notifications will be set to inactive [1]_.
There is also a management command to prune all devices failing to receive notifications:

.. code-block:: shell

	$ python manage.py prune_devices

This removes all devices which are not receiving notifications.

For more information, please refer to the APNS feedback service_.

.. _service: https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/CommunicatingWIthAPS.html

Exceptions
----------

- ``NotificationError(Exception)``: Base exception for all notification-related errors.
- ``gcm.GCMError(NotificationError)``: An error was returned by GCM. This is never raised when using bulk notifications.
- ``apns.APNSError(NotificationError)``: Something went wrong upon sending APNS notifications.
- ``apns.APNSDataOverflow(APNSError)``: The APNS payload exceeds its maximum size and cannot be sent.

Tastypie support
----------------

The app includes tastypie-compatible resources in push_notifications.api.tastypie. These can be used as-is, or as base classes
for more involved APIs.
The following resources are available:

- ``APNSDeviceResource``
- ``GCMDeviceResource``
- ``APNSDeviceAuthenticatedResource``
- ``GCMDeviceAuthenticatedResource``

The base device resources will not ask for authentication, while the authenticated ones will link the logged in user to
the device they register.
Subclassing the authenticated resources in order to add a ``SameUserAuthentication`` and a user ``ForeignKey`` is recommended.

When registered, the APIs will show up at ``<api_root>/device/apns`` and ``<api_root>/device/gcm``, respectively.

Django REST Framework (DRF) support
-----------------------------------

ViewSets are available for both APNS and GCM devices in two permission flavors:

- ``APNSDeviceViewSet`` and ``GCMDeviceViewSet``

	- Permissions as specified in settings (``AllowAny`` by default, which is not recommended)
	- A device may be registered without associating it with a user

- ``APNSDeviceAuthorizedViewSet`` and ``GCMDeviceAuthorizedViewSet``

	- Permissions are ``IsAuthenticated`` and custom permission ``IsOwner``, which will only allow the ``request.user`` to get and update devices that belong to that user
	- Requires a user to be authenticated, so all devices will be associated with a user

When creating an ``APNSDevice``, the ``registration_id`` is validated to be a 64-character or 200-character hexadecimal string. Since 2016, device tokens are to be increased from 32 bytes to 100 bytes.

Routes can be added one of two ways:

- Routers_ (include all views)
.. _Routers: http://www.django-rest-framework.org/tutorial/6-viewsets-and-routers#using-routers

::

	from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet, GCMDeviceAuthorizedViewSet
	from rest_framework.routers import DefaultRouter

	router = DefaultRouter()
	router.register(r'device/apns', APNSDeviceAuthorizedViewSet)
	router.register(r'device/gcm', GCMDeviceAuthorizedViewSet)

	urlpatterns = patterns('',
		# URLs will show up at <api_root>/device/apns
		url(r'^', include(router.urls)),
		# ...
	)

- Using as_view_ (specify which views to include)
.. _as_view: http://www.django-rest-framework.org/tutorial/6-viewsets-and-routers#binding-viewsets-to-urls-explicitly

::

	from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet

	urlpatterns = patterns('',
		# Only allow creation of devices by authenticated users
		url(r'^device/apns/?$', APNSDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_apns_device'),
		# ...
	)


Python 3 support
----------------

``django-push-notifications`` is fully compatible with Python 3.4 & 3.5

.. [1] Any devices which are not selected, but are not receiving notifications will not be deactivated on a subsequent call to "prune devices" unless another attempt to send a message to the device fails after the call to the feedback service.
