#!/usr/bin/env python

from setuptools import setup

setup(
    name='django-push-notifications',
    version='1.5.0',
    description='Send push notifications to mobile devices through GCM, APNS or WNS in Django',
    long_description=open('README.rst').read(),
    author='Jerome Leclanche',
    author_email='jerome@leclan.ch',
    url='https://github.com/jleclanche/django-push-notifications/',
    license='BSD',
    packages=['push_notifications'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django>=1.10',
        'apns2'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Networking',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
    ]
)
