# coding=utf-8
import hashlib
import os
import socket

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test-database.db'),
    },
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'push_notifications',
]

SECRET_KEY = hashlib.md5(socket.gethostname() + 'f@vn7)!i(shx=8*$cp-e_s&^@kc-3a0$it6ux@5$vb)51#7+p0').hexdigest()