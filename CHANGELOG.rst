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
