"""Test settings."""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Testing flag
TESTING = True

ALLOWED_HOSTS = ['*']

# Use file-based SQLite database for tests (allows migrations)
import os
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
    }
}

# Enable migrations for tests (required for database table creation)
# Note: While disabling migrations speeds up tests, it prevents tables from being created
# For this project, we keep migrations enabled to ensure proper database schema

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['null'],
            'level': 'CRITICAL',
        },
    },
}

# Disable CORS checks in tests
CORS_ALLOW_ALL_ORIGINS = True

