from .base import *

# Email backend para desenvolvimento (imprime emails no console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Adiciona o Django Debug Toolbar (opcional, mas recomendado)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Banco de Dados configurado via DATABASE_URL
DATABASES = {
    'default': env.db()
}