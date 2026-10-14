from .base import *

# Email backend para desenvolvimento (imprime emails no console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Banco de dados, em ordem de preferência:
#   1. DATABASE_URL (ex.: postgres://user:senha@localhost:5432/sm)
#   2. POSTGRES_* (mesmas variáveis usadas em produção)
#   3. SQLite local (db.sqlite3) -- funciona sem configurar nada.
if env('DATABASE_URL', default=None):
    DATABASES = {'default': env.db()}
elif env('POSTGRES_DB', default=None):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB'),
            'USER': env('POSTGRES_USER', default=''),
            'PASSWORD': env('POSTGRES_PASSWORD', default=''),
            'HOST': env('POSTGRES_HOST', default='localhost'),
            'PORT': env('POSTGRES_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
