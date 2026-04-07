import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

allowed_hosts_str = os.getenv("ALLOWED_HOSTS", default="*")

ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(",") if host]

JWT_PUBLIC_KEY = os.getenv("AUTH_PUBLIC_KEY")

JWT_ALGORITHM = "RS256"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL")

AUTH_SERVICE_URL=os.getenv("AUTH_SERVICE_URL")

INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET")
SERVICE_NAME = os.getenv("SERVICE_NAME")

SERVICE_NAME = "payment-service"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "drf_spectacular", 

    "payments",

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "config.middleware.request_id.RequestIDMiddleware",
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}


# Redis Cache

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


# DRF

REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SIMPLE_JWT = {

    "ALGORITHM": "RS256",
    "VERIFYING_KEY": JWT_PUBLIC_KEY,
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Payment Service API",
    "DESCRIPTION": "paymnet orchestration and checkout service",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}




LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "filters": {
        "service_name": {
            "()": "config.logging.filters.ServiceNameFilter",
        },
        "request_id": {
            "()": "config.logging.filters.RequestIDFilter",
        },

        # "trace_id": {
        # "()": "config.logging.filters.TraceIDFilter",
        # },
    },

    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": (
                "%(asctime)s %(levelname)s %(name)s "
                "%(service)s %(request_id)s %(message)s "
            ),
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["service_name", "request_id"],
        },
    },

    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


SERVICE_NAME = 'payment_service'