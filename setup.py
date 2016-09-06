#!/usr/bin/env python
import os.path
import push_notifications
from distutils.core import setup

README = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()

CLASSIFIERS = [
	"Development Status :: 5 - Production/Stable",
	"Environment :: Web Environment",
	"Framework :: Django",
	"Intended Audience :: Developers",
	"License :: OSI Approved :: MIT License",
	"Programming Language :: Python",
	"Programming Language :: Python :: 2.7",
	"Programming Language :: Python :: 3",
	"Programming Language :: Python :: 3.4",
	"Programming Language :: Python :: 3.5",
	"Topic :: Software Development :: Libraries :: Python Modules",
	"Topic :: System :: Networking",
]

setup(
	name="django-push-notifications-goinnn",
	packages=[
		"push_notifications",
		"push_notifications/api",
		"push_notifications/migrations",
		"push_notifications/management",
		"push_notifications/management/commands",
	],
	author=push_notifications.__author__,
	author_email=push_notifications.__email__,
	classifiers=CLASSIFIERS,
	description="Send push notifications to mobile devices through GCM or APNS in Django.",
	download_url="https://github.com/goinnn/django-push-notifications/tarball/master",
	long_description=README,
	url="https://github.com/goinnn/django-push-notifications",
	version=push_notifications.__version__,
)
