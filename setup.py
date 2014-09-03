#!/usr/bin/env python

# TODO - use find_packages rather than specifying

from setuptools import setup, find_packages

import os.path

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
    "Programming Language :: Python :: 3.4",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Networking",
]

import push_notifications

setup(
    # Minimum needed for setuptools
    name="django-push-notifications",
    version=push_notifications.__version__,
    package_dir={'': '.'},
    packages=["push_notifications", "push_notifications/migrations"],

    # Other stuff that's done
    install_requires=[
        "Django",
        "django-uuidfield"
    ],
    author=push_notifications.__author__,
    author_email=push_notifications.__email__,
    description="Send push notifications to mobile devices through GCM or APNS in Django.",
    license="MIT",
    url="https://github.com/jleclanche/django-push-notifications",
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.rst', 'LICENSE']
    },

    classifiers=CLASSIFIERS,
    download_url="https://github.com/jleclanche/django-push-notifications/tarball/master",
    long_description=README,
)
