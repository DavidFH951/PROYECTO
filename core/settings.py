"""
Django settings for core project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-yjda&xs)poheu686bol7)u0n3qde654mryzfe=&5oe)&@ukw^=")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1")

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Cloudinary para almacenamiento persistente en la nube
    "cloudinary_storage",
    "cloudinary",
    # Seguridad de intentos fallidos
    'axes',
    # Apps del proyecto
    "academia",
    # 2FA con TOTP
    'django_otp',
    'django_otp.plugins.otp_totp',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Entrega estáticos en producción
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'django_otp.middleware.OTPMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware de Axes (debe ir al final)
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "academia" / "templates",
            BASE_DIR / "academia" / "templates" / "componentes",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=60,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internacionalización
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# ARCHIVOS ESTÁTICOS (CSS, JavaScript, Imágenes del tema)
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Busca estáticos tanto en academia/static/ como en la raíz static/ si existe
STATICFILES_DIRS = [
    d for d in [BASE_DIR / "static", BASE_DIR / "academia/static"] if d.exists()
]

# ==============================================================================
# ARCHIVOS MEDIA (Subidos por usuarios / Cloudinary)
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

# Configuración de motores de almacenamiento
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage" if os.getenv('CLOUDINARY_API_KEY') else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Redirecciones de autenticación
LOGIN_URL = '/cuentas/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/cuentas/login/'

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend debe ser el primero
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Orígenes confiables para CSRF (incluyendo tu app en Render)
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.github.dev',
    'https://localhost:8000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD: INTENTOS DE LOGIN (DJANGO-AXES)
# ==============================================================================
AXES_FAILURE_LIMIT = 5                      # Bloquea al 5to intento fallido
AXES_COOLOFF_TIME = 0.25                    # Tiempo de bloqueo en horas (0.25 = 15 minutos)
AXES_RESET_ON_SUCCESS = True               # Reinicia el contador si inicia sesión correctamente
AXES_LOCKOUT_TEMPLATE = 'bloqueo_login.html' # Vista amigable de bloqueo
AXES_ENABLE_ADMIN = True                   # Permite desbloquear usuarios desde el /admin

# settings.py

# Cerrar la sesión si el navegador se cierra
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Tiempo de vida de la sesión (ej. 30 minutos de inactividad = 1800 segundos)
SESSION_COOKIE_AGE = 1800

# Renueva el tiempo de la cookie en cada petición activa
SESSION_SAVE_EVERY_REQUEST = True

# Prevenir acceso a cookies desde JavaScript (mitiga robo de sesión vía XSS)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# settings.py (ej. límite de 10 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

# ==============================================================================
# SEGURIDAD EN PRODUCCIÓN (Render + HTTPS)
# ==============================================================================
if not DEBUG:
    # 1. Indicar a Django que confíe en la cabecera HTTPS que envía el proxy de Render
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # 2. Forzar redirección a HTTPS
    SECURE_SSL_REDIRECT = True
    
    # 3. Cookies protegidas (solo viajan por HTTPS y no accesibles por JavaScript)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

    # 4. HSTS (Fuerza al navegador a usar siempre HTTPS)
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # 5. Prevención de ataques MIME y Clickjacking
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'