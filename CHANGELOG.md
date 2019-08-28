## 2.0.0 (unreleased)
* BACKWARDS-INCOMPATIBLE: Drop support for Django Rest Framework < 3.7
* BACKWARDS-INCOMPATIBLE: NotificationError is now moved from `__init__.py` to `exceptions.py`
    * Import with `from push_notifications.exceptions import NotificationError`
* PYTHON: Add support for Python 3.7
* APNS: Drop apns_errors, use exception class name instead
* FCM: Add FCM channels support for custom notification sound on Android Oreo
* BUGFIX: Fix error when send a message and the device is not active
* BUGFIX: Fix error when APN bulk messages sent with localized keys and badge function
* BUGFIX: Fix `Push failed: 403 fobidden` error when sending message to Chrome WebPushDevice


## 1.6.1 (2019-08-16)
* Pin dependency to apns to <0.6.0 to fix a Python version
  incompatibility.
* Add configuration for semi-automatic releases via Jazzband.

## 1.6.0 (2018-01-31)
* BACKWARDS-INCOMPATIBLE: Drop support for Django < 1.11
* DJANGO: Support Django 2.0
* NEW FEATURE: Add support for WebPush


## 1.5.0 (2017-04-16)
* BACKWARDS-INCOMPATIBLE: Remove `push_notifications.api.tastypie` module. Only DRF is supported now.
* BACKWARDS-INCOMPATIBLE: Drop support for Django < 1.10
* BACKWARDS-INCOMPATIBLE: Drop support for Django Rest Framework < 3.5
* DJANGO: Support Django 1.10, 1.11
* APNS: APNS is now supported using PyAPNS2 instead of an internal implementation.
* APNS: Stricter certificate validity checks
* APNS: Allow overriding the certfile from send_message()
* APNS: Add human-readable error messages
* APNS: Support thread-id in payload
* FCM: Add support for FCM (Firebase Cloud Messaging)
* FCM: Introduce `use_fcm_notification` option to enforce legacy GCM payload
* GCM: Add GCM_ERROR_TIMEOUT setting
* GCM: Fix support for sending GCM messages to topic subscribers
* WNS: Add support for WNS (Windows Notification Service)
* MISC: Make get_expired_tokens available in push_notifications.utils


## 1.4.1 (2016-01-11)
* APNS: Increased max device token size to 100 bytes (WWDC 2015, iOS 9)
* BUGFIX: Fix an index error in the admin


## 1.4.0 (2015-12-13)
* BACKWARDS-INCOMPATIBLE: Drop support for Python<3.4
* DJANGO: Support Django 1.9
* GCM: Handle canonical IDs
* GCM: Allow full range of GCMDevice.device_id values
* GCM: Do not allow duplicate registration_ids
* DRF: Work around empty boolean defaults issue (django-rest-framework#1101)
* BUGFIX: Do not throw GCMError in bulk messages from the admin
* BUGFIX: Avoid generating an extra migration on Python 3
* BUGFIX: Only send in bulk to active devices
* BUGFIX: Display models correctly in the admin on both Python 2 and 3


## 1.3.0 (2015-06-30)
* BACKWARDS-INCOMPATIBLE: Drop support for Python<2.7
* BACKWARDS-INCOMPATIBLE: Drop support for Django<1.8
* NEW FEATURE: Added a Django Rest Framework API. Requires DRF>=3.0.
* APNS: Add support for setting the ca_certs file with new APNS_CA_CERTIFICATES setting
* GCM: Deactivate GCMDevices when their notifications cause NotRegistered or InvalidRegistration
* GCM: Indiscriminately handle all keyword arguments in gcm_send_message and gcm_send_bulk_message
* GCM: Never fall back to json in gcm_send_message
* BUGFIX: Fixed migration issues from 1.2.0 upgrade.
* BUGFIX: Better detection of SQLite/GIS MySQL in various checks
* BUGFIX: Assorted Python 3 bugfixes
* BUGFIX: Fix display of device_id in admin


## 1.2.1 (2015-04-11)
* APNS, GCM: Add a db_index to the device_id field
* APNS: Use the native UUIDField on Django 1.8
* APNS: Fix timeout handling on Python 3
* APNS: Restore error checking on apns_send_bulk_message
* GCM: Expose the time_to_live argument in gcm_send_bulk_message
* GCM: Fix return value when gcm bulk is split in batches
* GCM: Improved error checking reliability
* GCM: Properly pass kwargs in GCMDeviceQuerySet.send_message()
* BUGFIX: Fix HexIntegerField for Django 1.3


## 1.2.0 (2014-10-07)
* BACKWARDS-INCOMPATIBLE: Added support for Django 1.7 migrations. South users will have to upgrade to South 1.0 or Django 1.7.
* APNS: APNS MAX_NOTIFICATION_SIZE is now a setting and its default has been increased to 2048
* APNS: Always connect with TLSv1 instead of SSLv3
* APNS: Implemented support for APNS Feedback Service
* APNS: Support for optional "category" dict
* GCM: Improved error handling in bulk mode
* GCM: Added support for time_to_live parameter
* BUGFIX: Fixed various issues relating HexIntegerField
* BUGFIX: Fixed issues in the admin with custom user models


## 1.1.0 (2014-06-29)
* BACKWARDS-INCOMPATIBLE: The arguments for device.send_message() have changed. See README.rst for details.
* Added a date_created field to GCMDevice and APNSDevice. This field keeps track of when the Device was created.
  This requires a `manage.py migrate`.
* Updated APNS protocol support
* Allow sending empty sounds on APNS
* Several APNS bugfixes
* Fixed BigIntegerField support on PostGIS
* Assorted migrations bugfixes
* Added a test suite


## 1.0.1 (2013-01-16)
* Migrations have been reset. If you were using migrations pre-1.0 you should upgrade to 1.0 instead and only
  upgrade to 1.0.1 when you are ready to reset your migrations.


## 1.0 (2013-01-15)
* Full Python 3 support
* GCM device_id is now a custom field based on BigIntegerField and always unsigned (it should be input as hex)
* Django versions older than 1.5 now require 'six' to be installed
* Drop uniqueness on gcm registration_id due to compatibility issues with MySQL
* Fix some issues with migrations
* Add some basic tests
* Integrate with travis-ci
* Add an AUTHORS file


## 0.9 (2013-12-17)
* Enable installation with pip
* Add wheel support
* Add full documentation
* Various bug fixes


## 0.8 (2013-03-15)
* Initial release
