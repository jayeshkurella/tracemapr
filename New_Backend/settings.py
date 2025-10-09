
from pathlib import Path

#from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-d!z9*n(x437=3uwjvdo#fezdgb!@ow!hql9dcbwah10t!$h1jx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'Mainapp',
    'corsheaders',
    'leaflet',
    'drf_yasg',
    'rest_framework',
    'user_management',
    'rest_framework_simplejwt.token_blacklist',
    # 'rest_framework.authtoken'



]




MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'New_Backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'New_Backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# local

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': 'New_Backend',
#         'USER': 'postgres',
#         'PASSWORD': 'Sanket@123',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# beta (testing)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': 'chhaya_beta_new1',
#         'USER': 'postgres',
#         'PASSWORD': 'postgres',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }


# production
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'chhaya_today',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# from .env file
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'


USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
import os
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = 'media/'

MEDIA_ROOT = '/home/administrator/chhaya-data/images'
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if os.name == 'nt':
    VENV_BASE = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo\\data\\proj')

# GDAL_LIBRARY_PATH = r'C:\Users\sanke\Desktop\coderize\TraceMapr\Chhaya_new_backend\env\Lib\site-packages\osgeo\gdal.dll'

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'https://.tracemapr.com',
    'http://.tracemapr.com',
    'http://localhost:4200',
    'https://products.coderize.in',
    'http://63.250.52.91',
    "https://beta.tracemapr.com",
]


CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS"
]

# Google Client ID
GOOGLE_CLIENT_ID ='229838098661-qhi912b4egncp89tqeihbsddpb7mjbud.apps.googleusercontent.com'


CSRF_TRUSTED_ORIGINS = [
    'https://products.coderize.in/chhaya/',
    'http://localhost:4200',
    'http://localhost:8080',
    'http://63.250.52.91',
    'https://.tracemapr.com',
    'http://.tracemapr.com'

]

AUTH_USER_MODEL = 'Mainapp.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]



# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.TokenAuthentication',  # Enable Token Authentication
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',  # Require authentication by default
#     ],
#     'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
# }
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
}
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),   # 1 day
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),      # 1 week
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),                 # default: Authorization: Bearer <token>
}

import datetime
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Generate dynamic log file names with date
today_date = datetime.datetime.now().strftime('%Y-%m-%d')





EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tracemapr@gmail.com'
EMAIL_HOST_PASSWORD = 'svud wnfa hbav sevy'
DEFAULT_FROM_EMAIL = 'tracemapr@gmail.com'


# local
# BACKEND_BASE_URL='http://127.0.0.1:8000/'
#
# beta
# BACKEND_BASE_URL = 'https://beta.tracemapr.com/backend'

# production
BACKEND_BASE_URL = 'https://tracemapr.com/backend'






# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }cd

#
# import os
# import logging
# from logging.handlers import TimedRotatingFileHandler
#
# LOG_DIR = os.path.join(BASE_DIR, 'logs')
# os.makedirs(LOG_DIR, exist_ok=True)  # ensure logs folder exists
#
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{asctime} [{levelname}] {name} - {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.handlers.TimedRotatingFileHandler',
#             'filename': os.path.join(LOG_DIR, 'django_app.log'),
#             'when': 'midnight',   # rotate daily at midnight
#             'interval': 1,
#             'backupCount': 30,    # keep last 30 days, delete older
#             'formatter': 'verbose',
#             'encoding': 'utf-8',
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file', 'console'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#         'Mainapp': {
#             'handlers': ['file', 'console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     },
# }
# import os
# import logging
# from logging.handlers import BaseRotatingHandler
# from datetime import datetime, timedelta
# import shutil
#
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#
# LOG_DIR = os.path.join(BASE_DIR, 'logs')
# os.makedirs(LOG_DIR, exist_ok=True)
#
#
# class DailyRotatingFileHandler(BaseRotatingHandler):
#     def __init__(self, filename, backupCount=30, encoding=None, delay=False):
#         self.backupCount = backupCount
#         self.baseFilename = filename
#         self.currentFileName = filename
#         self.encoding = encoding
#         super().__init__(self.currentFileName, 'a', encoding, delay)
#
#     def shouldRollover(self, record):
#         if not os.path.exists(self.currentFileName):
#             return False
#         file_time = datetime.fromtimestamp(os.path.getmtime(self.currentFileName))
#         return datetime.now().date() != file_time.date()
#
#     def doRollover(self):
#         if self.stream:
#             self.stream.close()
#             self.stream = None
#
#         yesterday = datetime.now() - timedelta(days=1)
#         old_filename = os.path.join(
#             os.path.dirname(self.baseFilename),
#             f"{yesterday.strftime('%Y-%m-%d')}.log"
#         )
#
#         if os.path.exists(self.currentFileName):
#             try:
#                 if os.path.exists(old_filename):
#                     os.remove(old_filename)  # prevent conflicts
#                 shutil.move(self.currentFileName, old_filename)  # safer on Windows
#             except PermissionError:
#                 # Fallback: append timestamp to avoid crash
#                 alt_filename = old_filename.replace(".log", f"_{int(datetime.now().timestamp())}.log")
#                 shutil.move(self.currentFileName, alt_filename)
#
#         # cleanup old files
#         if self.backupCount > 0:
#             for old_file in self.getFilesToDelete():
#                 try:
#                     os.remove(old_file)
#                 except OSError:
#                     pass
#
#         self.stream = self._open()
#
#     def getFilesToDelete(self):
#         dir_name, _ = os.path.split(self.baseFilename)
#         file_names = os.listdir(dir_name)
#         result = []
#
#         for file_name in file_names:
#             if len(file_name) == 14 and file_name.endswith(".log"):  # YYYY-MM-DD.log
#                 result.append(os.path.join(dir_name, file_name))
#
#         result.sort()
#         if len(result) > self.backupCount:
#             result = result[:len(result) - self.backupCount]
#         else:
#             result = []
#
#         return result
#
#
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{asctime} [{levelname}] {name} - {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'file': {
#             'level': 'DEBUG',
#             'class': 'New_Backend.settings.DailyRotatingFileHandler',  # adjust to your path
#             'filename': os.path.join(LOG_DIR, 'django_app.log'),
#             'backupCount': 30,
#             'formatter': 'verbose',
#             'encoding': 'utf-8',
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file', 'console'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#         'Mainapp': {
#             'handlers': ['file', 'console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     },
# }
import os
import logging
from logging.handlers import BaseRotatingHandler
from datetime import datetime, timedelta
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class DailyRotatingFileHandler(BaseRotatingHandler):
    """
    Custom daily log rotation:
    - Keeps current log in django_app.log (always today's log)
    - Copies yesterday's log to YYYY-MM-DD.log
    - Truncates django_app.log at rollover (avoids file locks on Windows)
    - Deletes logs older than backupCount
    """

    def __init__(self, filename, backupCount=30, encoding=None, delay=False):
        self.backupCount = backupCount
        self.baseFilename = filename
        self.currentFileName = filename
        self.encoding = encoding
        super().__init__(self.currentFileName, "a", encoding, delay)

    def shouldRollover(self, record):
        if not os.path.exists(self.currentFileName):
            return False
        file_time = datetime.fromtimestamp(os.path.getmtime(self.currentFileName))
        return datetime.now().date() != file_time.date()

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        yesterday = datetime.now() - timedelta(days=1)
        dated_filename = os.path.join(
            os.path.dirname(self.baseFilename),
            f"{yesterday.strftime('%Y-%m-%d')}.log",
        )

        if os.path.exists(self.currentFileName):
            try:
                # Copy current log → YYYY-MM-DD.log
                shutil.copy2(self.currentFileName, dated_filename)

                # Truncate django_app.log for today
                with open(self.currentFileName, "w", encoding=self.encoding or "utf-8"):
                    pass
            except Exception as e:
                print(f"Log rollover failed: {e}")

        # Cleanup old logs
        if self.backupCount > 0:
            for old_file in self.getFilesToDelete():
                try:
                    os.remove(old_file)
                except OSError:
                    pass

        self.stream = self._open()

    def getFilesToDelete(self):
        dir_name, _ = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        result = []

        for file_name in file_names:
            if file_name.endswith(".log") and len(file_name) == 14:  # YYYY-MM-DD.log
                result.append(os.path.join(dir_name, file_name))

        result.sort()
        if len(result) > self.backupCount:
            result = result[: len(result) - self.backupCount]
        else:
            result = []

        return result


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name} - {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "New_Backend.settings.DailyRotatingFileHandler",  # adjust path if needed
            "filename": os.path.join(LOG_DIR, "django_app.log"),
            "backupCount": 30,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "Mainapp": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
