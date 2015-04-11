v1.2.1 (2015-04-11)
===================
* APNS, GCM: Add a db_index to the device_id field
* APNS: Use the native UUIDField on Django 1.8
* APNS: Fix timeout handling on Python 3
* APNS: Restore error checking on apns_send_bulk_message
* GCM: Expose the time_to_live argument in gcm_send_bulk_message
* GCM: Fix return value when gcm bulk is split in batches
* GCM: Improved error checking reliability
* GCM: Properly pass kwargs in GCMDeviceQuerySet.send_message()
* BUGFIX: Fix HexIntegerField for Django 1.3

v1.2.0 (2014-10-07)
===================
* BACKWARDS-INCOMPATIBLE: Added support for Django 1.7 migrations. South users will have to upgrade to South 1.0 or Django 1.7.
* APNS: APNS MAX_NOTIFICATION_SIZE is now a setting and its default has been increased to 2048
* APNS: Always connect with TLSv1 instead of SSLv3
* APNS: Implemented support for APNS Feedback Service
* APNS: Support for optional "category" dict
* GCM: Improved error handling in bulk mode
* GCM: Added support for time_to_live parameter
* BUGFIX: Fixed various issues relating HexIntegerField
* BUGFIX: Fixed issues in the admin with custom user models

v1.1.0 (2014-06-29)
===================
* BACKWARDS-INCOMPATIBLE: The arguments for device.send_message() have changed. See README.rst for details.
* Added a date_created field to GCMDevice and APNSDevice. This field keeps track of when the Device was created.
  This requires a `manage.py migrate`.
* Updated APNS protocol support
* Allow sending empty sounds on APNS
* Several APNS bugfixes
* Fixed BigIntegerField support on PostGIS
* Assorted migrations bugfixes
* Added a test suite

v1.0.1 (2013-01-16)
===================
* Migrations have been reset. If you were using migrations pre-1.0 you should upgrade to 1.0 instead and only
  upgrade to 1.0.1 when you are ready to reset your migrations.

v1.0 (2013-01-15)
=================
* Full Python 3 support
* GCM device_id is now a custom field based on BigIntegerField and always unsigned (it should be input as hex)
* Django versions older than 1.5 now require 'six' to be installed
* Drop uniqueness on gcm registration_id due to compatibility issues with MySQL
* Fix some issues with migrations
* Add some basic tests
* Integrate with travis-ci
* Add an AUTHORS file

v0.9 (2013-12-17)
=================

* Enable installation with pip
* Add wheel support
* Add full documentation
* Various bug fixes

v0.8 (2013-03-15)
=================

* Initial release
