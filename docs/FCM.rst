Generate service account private key file
------------------------------

Migrating to FCM v1 API
------------------------------

- GCM and legacy FCM API support have been removed. (GCM is off since 2019, FCM legacy will be turned off in june 2024)
- Firebase-Admin SDK has been added


Authentication does not work with an access token anymore.
Follow the `official docs <https://firebase.google.com/docs/admin/setup/#initialize_the_sdk_in_non-google_environments>`_ to generate a service account private key file.

Then, either define an environment variable ``GOOGLE_APPLICATION_CREDENTIALS`` with the path to the service account private key file, or pass the path to the file explicitly when initializing the SDK.

Initialize the firebase admin in your ``settings.py`` file.

.. code-block:: python

	# Import the firebase service
	import firebase_admin

	# Initialize the default app
	default_app = firebase_admin.initialize_app()


This will do the trick.


Multiple Application Support
------------------------------

Removed settings:

- ``API_KEY``
- ``POST_URL``
- ``ERROR_TIMEOUT``

Added setting:

- ``FIREBASE_APP``: initialise your firebase app and set it here.


.. code-block:: python

	# Before
	PUSH_NOTIFICATIONS_SETTINGS = {
		# Load and process all PUSH_NOTIFICATIONS_SETTINGS using the AppConfig manager.
		"CONFIG": "push_notifications.conf.AppConfig",

		# collection of all defined applications
		"APPLICATIONS": {
			"my_fcm_app": {
				# PLATFORM (required) determines what additional settings are required.
				"PLATFORM": "FCM",

				# required FCM setting
				"API_KEY": "[your api key]",
			},
			"my_ios_app": {
				  # PLATFORM (required) determines what additional settings are required.
				  "PLATFORM": "APNS",

				  # required APNS setting
				  "CERTIFICATE": "/path/to/your/certificate.pem",
			},
			"my_wns_app": {
				# PLATFORM (required) determines what additional settings are required.
				"PLATFORM": "WNS",

				# required WNS settings
				"PACKAGE_SECURITY_ID": "[your package security id, e.g: 'ms-app://e-3-4-6234...']",
				"SECRET_KEY": "[your app secret key, e.g.: 'KDiejnLKDUWodsjmewuSZkk']",
			},
		}
	}

	# After

	firebase_app = firebase_admin.initialize_app()

	PUSH_NOTIFICATIONS_SETTINGS = {
		# Load and process all PUSH_NOTIFICATIONS_SETTINGS using the AppConfig manager.
		"CONFIG": "push_notifications.conf.AppConfig",

		# collection of all defined applications
		"APPLICATIONS": {
			"my_fcm_app": {
				# PLATFORM (required) determines what additional settings are required.
				"PLATFORM": "FCM",

				# FCM settings
				"FIREBASE_APP": firebase_app,
			},
			"my_ios_app": {
				  # PLATFORM (required) determines what additional settings are required.
				  "PLATFORM": "APNS",

				  # required APNS setting
				  "CERTIFICATE": "/path/to/your/certificate.pem",
			},
			"my_wns_app": {
				# PLATFORM (required) determines what additional settings are required.
				"PLATFORM": "WNS",

				# required WNS settings
				"PACKAGE_SECURITY_ID": "[your package security id, e.g: 'ms-app://e-3-4-6234...']",
				"SECRET_KEY": "[your app secret key, e.g.: 'KDiejnLKDUWodsjmewuSZkk']",
			},
		}
	}
