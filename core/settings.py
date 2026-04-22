"""
Django settings for core project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные окружения из файла .env
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# --- АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПАПКИ ЛОГОВ ---
LOGS_DIR = BASE_DIR / 'logs'
if not LOGS_DIR.exists():
    os.makedirs(LOGS_DIR)
# -------------------------------------------

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("Отсутствует SECRET_KEY! Проверьте файл .env")

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = allowed_hosts_env.split(',')

# Application definition
INSTALLED_APPS =[
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'axes', 
    'mathfilters',
    'crm',  
    'import_export', 
]

MIDDLEWARE =[
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES =[
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors':[
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Подключаем PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'crm_db'),
        'USER': os.environ.get('DB_USER', 'crm_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

AUTHENTICATION_BACKENDS =[
    'axes.backends.AxesBackend', 
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS =[
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS =[os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Настройки системы входа/выхода
LOGIN_URL = 'login'              
LOGIN_REDIRECT_URL = '/'         
LOGOUT_REDIRECT_URL = 'login'    

# AXES
AXES_FAILURE_LIMIT = 5            
AXES_COOLOFF_TIME = 1             
AXES_LOCKOUT_TEMPLATE = None      
AXES_RESET_ON_SUCCESS = True      

# SECURE COOKIES
USE_SECURE_COOKIES = os.environ.get('SECURE_COOKIES', 'False') == 'True'
SESSION_COOKIE_SECURE = USE_SECURE_COOKIES
CSRF_COOKIE_SECURE = USE_SECURE_COOKIES

# ЛОГИРОВАНИЕ
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            # Используем переменную LOGS_DIR, которую определили выше
            'filename': os.path.join(LOGS_DIR, 'django_errors.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}