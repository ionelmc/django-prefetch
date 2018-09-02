# -*- coding: utf-8 -*-
import os

DEBUG = True

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'database.sqlite')
SECONDARY_DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'database-secondary.sqlite')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_NAME
    },
    'secondary': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SECONDARY_DATABASE_NAME
    }
}
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'test_app',
)
SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

SECRET_KEY = "DON'T MATTER"
