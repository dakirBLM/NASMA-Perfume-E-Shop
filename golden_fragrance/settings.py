import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'sk_test_51SEr5IEJ1eApDxY43f8kYVhd5vtojpS9CwvD0kySMfcZ72IpB0ed17hrkDB8iT7EC2Np6vCiC5yiKB4h7pguwubz00q8RDmIQB'
DEBUG = True
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,silvadakir.pythonanywhere.com').split(',')
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'silvadakir.pythonanywhere.com')

INSTALLED_APPS = [
    # modeltranslation must load before admin to patch models/forms
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'products',
    'accounts',
    'orders',


]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'golden_fragrance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'products.context_processors.categories_collections',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]
STATIC_ROOT = BASE_DIR / "staticfiles"


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization / Model translations
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'en')
LANGUAGES = (
    ('en', 'English'),
    ('ar', 'Arabic'),
    ('cs', 'Czech'),
    ('pl', 'Polish'),
)
LOCALE_PATHS = [BASE_DIR / 'locale']
# django-modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE

STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51SEr5IEJ1eApDxY4p1oyyyeosibB4klGqw1wdyrcnwGQeeMKqWqlUU4zgX1mqs7F1R8xiMmnbbOMhp37CbyEzOjq00REd9rORs')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51SEr5IEJ1eApDxY43f8kYVhd5vtojpS9CwvD0kySMfcZ72IpB0ed17hrkDB8iT7EC2Np6vCiC5yiKB4h7pguwubz00q8RDmIQB')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')


# Email settings (SendGrid by default; fall back to console if missing key)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'apikey')  # literal string "apikey" for SendGrid
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@goldenfragrance.example')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'dakirblm@gmail.com')

# Choose backend based on availability of credentials
if EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
else:
    # Helpful for local development when no credentials are provided
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'