django-push-notifications
=========================
.. image:: https://api.travis-ci.org/jleclanche/django-push-notifications.png
	:target: https://travis-ci.org/jleclanche/django-push-notifications

A minimal Django app that implements Device models that can send messages through APNS, FCM/GCM and WNS.

The app implements three models: ``GCMDevice``, ``APNSDevice`` and ``WNSDevice``. Those models share the same attributes:
 - ``name`` (optional): A name for the device.
 - ``active`` (default True): A boolean that determines whether the device will be sent notifications.
 - ``user`` (optional): A foreign key to auth.User, if you wish to link the device to a specific user.
 - ``device_id`` (optional): A UUID for the device obtained from Android/iOS/Windows APIs, if you wish to uniquely identify it.
 - ``registration_id`` (required): The FCM/GCM registration id or the APNS token for the device.


The app also implements an admin panel, through which you can test single and bulk notifications. Select one or more
FCM/GCM, APNS or WNS devices and in the action dropdown, select "Send test message" or "Send test message in bulk", accordingly.
Note that sending a non-bulk test message to more than one device will just iterate over the devices and send multiple
single messages.

Dependencies
------------
- Python 2.7 or 3.4+
- Django 1.10+
- For the API module, Django REST Framework 3.5+ is required.

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
		"FCM_API_KEY": "[your api key]",
		"GCM_API_KEY": "[your api key]",
		"APNS_CERTIFICATE": "/path/to/your/certificate.pem",
		"APNS_TOPIC": "com.example.push_test",
		"WNS_PACKAGE_SECURITY_ID": "[your package security id, e.g: 'ms-app://e-3-4-6234...']",
		"WNS_SECRET_KEY": "[your app secret key, e.g.: 'KDiejnLKDUWodsjmewuSZkk']",
	}

.. note::
	If you are planning on running your project with ``APNS_USE_SANDBOX=True``, then make sure you have set the
	*development* certificate as your ``APNS_CERTIFICATE``. Otherwise the app will not be able to connect to the correct host. See settings_ for details.

You can learn more about APNS certificates `here <https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/ApplePushService.html>`_.

Native Django migrations are in use. ``manage.py migrate`` will install and migrate all models.

.. _settings:

Settings list
-------------
All settings are contained in a ``PUSH_NOTIFICATIONS_SETTINGS`` dict.

In order to use FCM/GCM, you are required to include ``FCM_API_KEY`` or ``GCM_API_KEY``.
For APNS, you are required to include ``APNS_CERTIFICATE``.
For WNS, you need both the ``WNS_PACKAGE_SECURITY_KEY`` and the ``WNS_SECRET_KEY``.

**APNS settings**

- ``APNS_CERTIFICATE``: Absolute path to your APNS certificate file. Certificates with passphrases are not supported.
- ``APNS_TOPIC``: The topic of the remote notification, which is typically the bundle ID for your app. If you omit this header and your APNs certificate does not specify multiple topics, the APNs server uses the certificate’s Subject as the default topic.
- ``APNS_USE_ALTERNATIVE_PORT``: Use port 2197 for APNS, instead of default port 443.
- ``APNS_USE_SANDBOX``: Use 'api.development.push.apple.com', instead of default host 'api.push.apple.com'.

**FCM/GCM settings**

- ``FCM_API_KEY``: Your API key for Firebase Cloud Messaging.
- ``FCM_POST_URL``: The full url that FCM notifications will be POSTed to. Defaults to https://fcm.googleapis.com/fcm/send.
- ``FCM_MAX_RECIPIENTS``: The maximum amount of recipients that can be contained per bulk message. If the ``registration_ids`` list is larger than that number, multiple bulk messages will be sent. Defaults to 1000 (the maximum amount supported by FCM).
- ``FCM_ERROR_TIMEOUT``: The timeout on FCM POSTs.
- ``GCM_API_KEY``, ``GCM_POST_URL``, ``GCM_MAX_RECIPIENTS``, ``GCM_ERROR_TIMEOUT``: Same parameters for GCM

**WNS settings**

- ``WNS_PACKAGE_SECURITY_KEY``: TODO
- ``WNS_SECRET_KEY``: TODO


- ``USER_MODEL``: Your user model of choice. Eg. ``myapp.User``. Defaults to ``settings.AUTH_USER_MODEL``.
- ``UPDATE_ON_DUPLICATE_REG_ID``: Transform create of an existing Device (based on registration id) into a update. See below `Update of device with duplicate registration ID`_ for more details.

Sending messages
----------------
FCM/GCM and APNS services have slightly different semantics. The app tries to offer a common interface for both when using the models.

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
	device.send_message(None, content_available=1, extra={"foo": "bar"}) # Silent message with custom data.
	# alert with title and body.
	device.send_message(message={"title" : "Game Request", "body" : "Bob wants to play poker"}, extra={"foo": "bar"})
	device.send_message("Hello again", thread_id="123", extra={"foo": "bar"}) # set thread-id to allow iOS to merge notifications

.. note::
	APNS does not support sending payloads that exceed 2048 bytes (increased from 256 in 2014).
	The message is only one part of the payload, if
	once constructed the payload exceeds the maximum size, an ``APNSDataOverflow`` exception will be raised before anything is sent.
  Reference: `Apple Payload Documentation <https://developer.apple.com/library/content/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CreatingtheNotificationPayload.html#//apple_ref/doc/uid/TP40008194-CH10-SW1>`_

Sending messages in bulk
------------------------
.. code-block:: python

	from push_notifications.models import APNSDevice, GCMDevice

	devices = GCMDevice.objects.filter(user__first_name="James")
	devices.send_message("Happy name day!")

Sending messages in bulk makes use of the bulk mechanics offered by GCM and APNS. It is almost always preferable to send
bulk notifications instead of single ones.

It's also possible to pass badge parameter as a function which accepts token parameter in order to set different badge
value per user. Assuming User model has a method get_badge returning badge count for a user:

.. code-block:: python

	devices.send_message(
		"Happy name day!",
		badge=lambda token: APNSDevice.objects.get(registration_id=token).user.get_badge()
	)

Firebase vs Google Cloud Messaging
----------------------------------

``django-push-notifications`` supports both Google Cloud Messaging and Firebase Cloud Messaging (which is now the officially supported messaging platform from Google). When registering a device, you must pass the ``cloud_type`` parameter to set the cloud type that matches the device needs.
This is currently defaulting to ``'GCM'``, but may change to ``'FCM'`` at some point. You are encouraged to use the `officially supported library <https://developers.google.com/cloud-messaging/faq>`_.

When using FCM, ``django-push-notifications`` will automatically use the `notification and data messages format <https://firebase.google.com/docs/cloud-messaging/concept-options#notifications_and_data_messages>`_ to be conveniently handled by Firebase devices. You may want to check the payload to see if it matches your needs, and review your notification statuses in `FCM Diagnostic console <https://support.google.com/googleplay/android-developer/answer/2663268?hl=en>`_.


.. code-block:: python

	# Create a FCM device
	fcm_device = GCMDevice.objects.create(registration_id="token", cloud_message_type="FCM", user=the_user)

	# Send a notification message
	fcm_device.send_message("This is a message")

	# Send a notification message with additionnal payload
	fcm_device.send_message("This is a enriched message", extra={"title": "Notification title", "icon": "icon_ressource"})

	# Send a notification message with additionnal payload (alternative syntax)
	fcm_device.send_message("This is a enriched message", title="Notification title", badge=6)

	# Send a notification message with extra data
	fcm_device.send_message("This is a message with data", extra={"other": "content", "misc": "data"})

	# Send a notification message with options
	fcm_device.send_message("This is a message", time_to_live=3600)

	# Send a data message only
	fcm_device.send_message(None, extra={"other": "content", "misc": "data"})

You can disable this default behaviour by setting ``use_fcm_notifications`` to ``False``.

.. code-block:: python

	fcm_device = GCMDevice.objects.create(registration_id="token", cloud_message_type="FCM", user=the_user)

	# Send a data message with classic format
	fcm_device.send_message("This is a message", use_fcm_notifications=False)


Sending FCM/GCM messages to topic members
-----------------------------------------
FCM/GCM topic messaging allows your app server to send a message to multiple devices that have opted in to a particular topic. Based on the publish/subscribe model, topic messaging supports unlimited subscriptions per app. Developers can choose any topic name that matches the regular expression, "/topics/[a-zA-Z0-9-_.~%]+".
Note: gcm_send_bulk_message must be used when sending messages to topic subscribers, and setting the first param to any value other than None will result in a 400 Http error.

.. code-block:: python

	from push_notifications.gcm import send_message

        # First param is "None" because no Registration_id is needed, the message will be sent to all devices subscribed to the topic.
        send_message(None, {"body": "Hello members of my_topic!"}, to="/topics/my_topic")

Reference: `FCM Documentation <https://firebase.google.com/docs/cloud-messaging/android/topic-messaging>`_

Exceptions
----------

- ``NotificationError(Exception)``: Base exception for all notification-related errors.
- ``gcm.GCMError(NotificationError)``: An error was returned by GCM. This is never raised when using bulk notifications.
- ``apns.APNSError(NotificationError)``: Something went wrong upon sending APNS notifications.
- ``apns.APNSDataOverflow(APNSError)``: The APNS payload exceeds its maximum size and cannot be sent.

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

Update of device with duplicate registration ID
-----------------------------------------------

The DRF viewset enforce the uniqueness of the registration ID. In same use case it
may cause issue: If an already registered mobile change its user and it will
fail to register because the registration ID already exist.

When option ``UPDATE_ON_DUPLICATE_REG_ID`` is set to True, then any creation of
device with an already existing registration ID will be transformed into an update.

The ``UPDATE_ON_DUPLICATE_REG_ID`` only works with DRF.


.. [1] Any devices which are not selected, but are not receiving notifications will not be deactivated on a subsequent call to "prune devices" unless another attempt to send a message to the device fails after the call to the feedback service.
