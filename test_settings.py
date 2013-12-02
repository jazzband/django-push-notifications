# coding=utf-8
import hashlib
import os
import socket

DEBUG = True
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test-database.db'),
    },
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    'push_notifications',
]

SECRET_KEY = hashlib.md5(socket.gethostname() + 'f@vn7)!i(shx=8*$cp-e_s&^@kc-3a0$it6ux@5$vb)51#7+p0').hexdigest()

TEST_ID_ANDROID = 'gJ6YMGzkgSlPEkltUxXD9rGeHiNFvEncsKvu' \
                  'jddDTdf5399FghAv2rr1HH5qUgHTpoNSgSF3' \
                  'CEaHA3P1HbuhJApL0ZHTe_uFYRoK3hfSoH7v' \
                  'M0AIcPmNCHnibEUAoIpPonrt62hmISh3xD9O' \
                  '-S0hQrKJjBbC0RKBrs'
TEST_ID_APPLE = 'ab3c5d6726e5fd6738f982b3bc635b2d'

PUSH_NOTIFICATIONS_SETTINGS = {
    "GCM_API_KEY": "FAKE_KEY",
    "APNS_CERTIFICATE": __file__,
}