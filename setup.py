#!/usr/bin/env python

import os.path
from distutils.core import setup

README = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()

CLASSIFIERS = [
	"Development Status :: 3 - Alpha",
	"Environment :: Web Environment",
	"Framework :: Django",
	"Intended Audience :: Developers",
	"License :: OSI Approved :: MIT License",
	"Programming Language :: Python",
	"Topic :: Software Development :: Libraries :: Python Modules",
	"Topic :: System :: Networking",
]

VERSION = "0.8"

setup(
	name = "django-push-notifications",
	packages = ["push_notifications"],
	author = "Jerome Leclanche",
	author_email = "jerome.leclanche+pypi@gmail.com",
	classifiers = CLASSIFIERS,
	description = "Send push notifications to mobile devices through GCM or APNS in Django.",
	download_url = "https://github.com/Adys/django-push-notifications/tarball/master",
	long_description = README,
	url = "https://github.com/Adys/django-push-notifications",
	version = VERSION,
)
