# Django settings for the MemorySim project
# This file contains all the configuration settings for the Django application

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# TODO: Move this to environment variables in production
SECRET_KEY = 'django-insecure-please_change_this_key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# List of allowed hosts that can serve this Django application
ALLOWED_HOSTS = ['*']

# CORS settings for development - allows all origins for frontend integration
CORS_ALLOW_ALL_ORIGINS = True

# Application definition - Django apps installed in this project
INSTALLED_APPS = [
    # Default Django admin interface
    'django.contrib.admin',
    # Django authentication system
    'django.contrib.auth',
    # Django content types framework
    'django.contrib.contenttypes',
    # Django sessions framework
    'django.contrib.sessions',
    # Django messaging framework
    'django.contrib.messages',
    # Static files handling
    'django.contrib.staticfiles',

    # Third-party apps
    'corsheaders',
    'channels',          # NEW: add Django Channels for realtime support

    # Custom apps
    'api',
    'core',
]

# Middleware stack - processes requests and responses in order
MIDDLEWARE = [
    # CORS middleware must be at the top to handle cross-origin requests
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Security middleware for security headers
    'django.middleware.security.SecurityMiddleware',
    # Session middleware for user sessions
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # CSRF protection middleware
    'django.middleware.csrf.CsrfViewMiddleware',
    # Authentication middleware for user authentication
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Messages middleware for displaying messages to users
    'django.contrib.messages.middleware.MessageMiddleware',
    # Clickjacking protection middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration module
ROOT_URLCONF = 'memory_sim.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Template directories - looks for templates in the templates folder
        'DIRS': [BASE_DIR / 'templates'],
        # Allow apps to have their own template directories
        'APP_DIRS': True,
        'OPTIONS': {
            # Context processors that add variables to template context
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application configuration for deployment
WSGI_APPLICATION = 'memory_sim.wsgi.application'

# --- Channels / ASGI configuration (for realtime websocket) ---
ASGI_APPLICATION = 'memory_sim.asgi.application'

# Channel layers - in-memory is fine for single server / kiosk usage
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# --- Storyline game configuration ---
# Single-room settings (museum / kiosk mode)
MUSEUM_ROOM_ID = os.environ.get("MUSEUM_ROOM_ID", "MUSEUM")
# Require both players to press "ready" to start (falls back to 1 if only one connected)
MIN_READY_TO_START = 2
# Require both players to choose before resolving (falls back to 1 if only one connected)
MIN_CHOICES_TO_DECIDE = 2

# Database configuration (using SQLite for development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation settings for user authentication
AUTH_PASSWORD_VALIDATORS = [
    {
        # Prevents passwords that are too similar to user information
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # Enforces minimum password length
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        # Prevents commonly used passwords
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # Prevents purely numeric passwords
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization settings
LANGUAGE_CODE = 'en-us'
# Set timezone to Brisbane for Australian deployment
TIME_ZONE = 'Australia/Brisbane'
# Enable internationalization
USE_I18N = True
# Use timezone-aware datetimes
USE_TZ = True

# Static files configuration (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type for models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
