#!/usr/bin/env python
import os
import sys
import unittest


def setup():
	# add test/src folders to sys path
	test_folder = os.path.abspath(os.path.dirname(__file__))
	src_folder = os.path.abspath(os.path.join(test_folder, os.pardir))
	sys.path.insert(0, test_folder)
	sys.path.insert(0, src_folder)

	# define settings
	import django.conf
	os.environ[django.conf.ENVIRONMENT_VARIABLE] = "settings"

	# set up environment
	from django.test.utils import setup_test_environment
	setup_test_environment()

	# See https://docs.djangoproject.com/en/dev/releases/1.7/#app-loading-changes
	import django
	if django.VERSION >= (1, 7, 0):
		django.setup()

	# set up database
	from django.db import connection
	connection.creation.create_test_db()


def tear_down():
	# destroy test database
	from django.db import connection
	connection.creation.destroy_test_db("not_needed")

	# teardown environment
	from django.test.utils import teardown_test_environment
	teardown_test_environment()


# fire in the hole!
if __name__ == "__main__":
	setup()

	import tests
	unittest.main(module=tests)

	tear_down()
