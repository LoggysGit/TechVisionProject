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

    'logic.apps.LogicConfig',
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

STATIC_URL = 'static/'

# = Custom definitions = #
LOGIC_CONF_DIR = BASE_DIR / 'config'

LLM_DOWNLOAD_URL = "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf"

LAW_DB_PATH = "..\\backend\\law_db\\"
LAW_PDF_PATH = "..\\backend\\config\\law.pdf"

CENSOR_MODEL = LOGIC_CONF_DIR / 'Qwen2.5.gguf'
SEN_TRANSFORMER_MODEL = 'intfloat/multilingual-e5-small'

MODEL_CONTEXT = 4096

GROQ_KEY = env('GROQ_API_KEY')

GROQ_MODELS = {
    'fast': 'llama-3.3-70b-versatile',
    'smart': 'llama-3.3-70b-versatile'
}
LAW_ARTICLES = {
    'fast': 4,
    'smart': 7
}