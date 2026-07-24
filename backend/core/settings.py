""" Django settings for core project. """

import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# = Load .env file = #
env = environ.Env()
environ.Env.read_env(os.path.join(ROOT_DIR, '.env'))

# = Private definition = #
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.get_value('DEBUG', cast=bool, default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# = Application definition = #
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# = Defaunt DATABASES setting = #
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

# = Internationalization = #
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# = Custom definitions = #
LOGIC_CONF_DIR = BASE_DIR / 'config'

LAW_DB_PATH = "..\\backend\\law_db\\"
LAW_PDF_PATH = "..\\backend\\config\\law.pdf"

CENSOR_MODEL = LOGIC_CONF_DIR / 'Qwen2.5.gguf'
SEN_TRANSFORMER_MODEL = 'intfloat/multilingual-e5-small'

MODEL_CONTEXT = 3120

GROQ_KEY = env('GROQ_API_KEY')

GROQ_MODELS = {
    'fast': 'llama-3.1-8b-instant',
    'smart': 'llama-3.3-70b-versatile'
}