v1.0 (2013-01-16)
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
