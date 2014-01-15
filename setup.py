#!/usr/bin/env python

import os.path
from distutils.core import setup

README = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()

CLASSIFIERS = [
	"Development Status :: 5 - Production/Stable",
	"Environment :: Web Environment",
	"Framework :: Django",
	"Intended Audience :: Developers",
	"License :: OSI Approved :: MIT License",
	"Programming Language :: Python",
	"Programming Language :: Python :: 2.6",
	"Programming Language :: Python :: 2.7",
	"Programming Language :: Python :: 3",
	"Programming Language :: Python :: 3.3",
	"Topic :: Software Development :: Libraries :: Python Modules",
	"Topic :: System :: Networking",
]


import push_notifications

setup(
	name = "django-push-notifications",
	packages = ["push_notifications", "push_notifications/migrations"],
	author = push_notifications.__author__,
	author_email = push_notifications.__email__,
	classifiers = CLASSIFIERS,
	description = "Send push notifications to mobile devices through GCM or APNS in Django.",
	download_url = "https://github.com/Adys/django-push-notifications/tarball/master",
	long_description = README,
	url = "https://github.com/Adys/django-push-notifications",
	version = push_notifications.__version__,
)
