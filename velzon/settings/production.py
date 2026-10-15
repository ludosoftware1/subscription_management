from .base import *

# --- Segurança -----------------------------------------------------------
# O padrão exige HTTPS (proxy com TLS na frente do container). Em acesso HTTP
# direto (ex.: http://ip:8001), defina as três variáveis como "False" no .env;
# caso contrário o cookie de sessão não é enviado e o login "não pega".
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS só é emitido em respostas HTTPS, então é inofensivo num deploy HTTP.
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# Origens aceitas nos POSTs (com esquema). Se não informado, usa a origem de SITE_URL.
CSRF_TRUSTED_ORIGINS = [o for o in env.list('CSRF_TRUSTED_ORIGINS', default=[]) if o]
if not CSRF_TRUSTED_ORIGINS and SITE_URL.startswith(('http://', 'https://')):
    CSRF_TRUSTED_ORIGINS = [SITE_URL.rstrip('/')]

# --- Banco de dados ------------------------------------------------------
# DATABASE_URL tem precedência; senão, POSTGRES_* são obrigatórias.
# Dentro do container, o Postgres do servidor é alcançado por host.docker.internal.
if env('DATABASE_URL', default=None):
    DATABASES = {'default': env.db()}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB'),
            'USER': env('POSTGRES_USER'),
            'PASSWORD': env('POSTGRES_PASSWORD'),
            'HOST': env('POSTGRES_HOST'),
            'PORT': env('POSTGRES_PORT', default='5432'),
        }
    }
DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=60)
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
aplicar_schema_postgres(DATABASES['default'])

# --- E-mail --------------------------------------------------------------
# A recuperação de senha usa a API externa de notificação (apps.email_app),
# configurada por NOTIFICATION_API_URL / API_AUTH_TOKEN no .env.
