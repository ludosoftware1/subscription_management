import os
import re
import environ
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Inicializa o django-environ
env = environ.Env(
    DEBUG=(bool, False) # Define o tipo e o valor padrão para DEBUG
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR agora aponta para a raiz do projeto (onde está o manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Lê o arquivo .env
environ.Env.read_env(BASE_DIR / '.env')

# --- Variáveis de Ambiente ---

# Lê a versão da aplicação do ambiente, com 'dev' como valor padrão.
APP_VERSION = env('APP_VERSION', default='dev')

# Chave secreta é lida do ambiente
SECRET_KEY = env('SECRET_KEY')

# Debug é lido do ambiente
DEBUG = env('DEBUG')

# Hosts permitidos são lidos do ambiente
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# URL base do site para uso em e-mails e outras referências
SITE_URL = env('SITE_URL', default='http://localhost:8000')
# URL do logo para uso em e-mails
LOGO_URL = env('LOGO_URL', default=None)

# Tokens e URL para a API de Notificação Externa
NOTIFICATION_API_URL = env('NOTIFICATION_API_URL', default='https://notification-center.onrender.com/api/v1/email/send-email')
API_AUTH_TOKEN = env('API_AUTH_TOKEN', default='default-api-key-from-settings')
NOTIFICATION_WEBHOOK_TOKEN = env('NOTIFICATION_WEBHOOK_TOKEN', default='default-webhook-token-from-settings')

# --- Integração com o SynDoc (API /api/tenants/, ver apps/tenants/services.py) ---
# URL por onde este servidor alcança o SynDoc (pública ou interna do Docker).
SAAS_API_BASE_URL = env('SAAS_API_BASE_URL', default=None)
# Mesma chave do SAAS_API_KEY no .env do SynDoc.
SAAS_API_KEY = env('SAAS_API_KEY', default=None)
# Host administrativo cadastrado no SynDoc (SAAS_API_HOSTS de lá). Enviado no
# cabeçalho Host quando a chamada é interna (ex.: http://host.docker.internal:8010).
SAAS_API_HOST_HEADER = env('SAAS_API_HOST_HEADER', default=None)
# "https" faz o SynDoc tratar a chamada interna como segura (SECURE_SSL_REDIRECT).
SAAS_API_FORWARDED_PROTO = env('SAAS_API_FORWARDED_PROTO', default=None)
SAAS_API_TIMEOUT = env.int('SAAS_API_TIMEOUT', default=15)
# Criar tenant = CREATE SCHEMA + todas as migrations do SynDoc; pode levar minutos.
# Deve ser MENOR que o timeout do Gunicorn deste painel (GUNICORN_TIMEOUT).
SAAS_API_CREATE_TIMEOUT = env.int('SAAS_API_CREATE_TIMEOUT', default=300)
SAAS_API_VERIFY_SSL = env.bool('SAAS_API_VERIFY_SSL', default=True)

# --- Schema próprio no Postgres ------------------------------------------
# Permite que o painel fique no MESMO banco do SynDoc sem tocar no schema
# public dele (que guarda users_client/users_domain de todos os clientes).
# Com POSTGRES_SCHEMA definido, todas as tabelas do painel vão para esse schema
# (search_path) e o entrypoint o cria antes do migrate (verificar_banco).
# Vazio = usa o schema padrão do banco (o certo para um banco exclusivo do painel).
POSTGRES_SCHEMA = env('POSTGRES_SCHEMA', default='').strip()
if POSTGRES_SCHEMA:
    if not re.fullmatch(r'[a-z_][a-z0-9_]{0,62}', POSTGRES_SCHEMA):
        raise ImproperlyConfigured(
            "POSTGRES_SCHEMA deve ter só letras minúsculas, números e _ (máx. 63), começando por letra ou _."
        )
    if POSTGRES_SCHEMA == 'public' or POSTGRES_SCHEMA.startswith('pg_'):
        raise ImproperlyConfigured(
            "POSTGRES_SCHEMA não pode ser 'public' nem começar com 'pg_'; use um nome próprio, ex.: painel_assinaturas."
        )


def aplicar_schema_postgres(database):
    """Fixa o search_path da conexão no schema do painel (só Postgres)."""
    if POSTGRES_SCHEMA and 'postgresql' in database.get('ENGINE', ''):
        options = database.setdefault('OPTIONS', {})
        options['options'] = f"-c search_path={POSTGRES_SCHEMA}"
    return database


# --- Configurações Comuns do Django (copiadas do seu settings.py) ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # allauth providers
    'allauth.socialaccount.providers.google',

    # Local apps
    'layouts',
    'components',
    'apps.perfil',
    'apps.core',
    'apps.configuracao',
    'apps.notificacoes',
    'apps.tenants',
    'pages',



    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap4',
    'crispy_bootstrap5', # Adicionado para compatibilidade com Bootstrap 5
    'multiselectfield',
    'widget_tweaks',
    
    #Audit Trail
    'auditlog',
    
    # Feedback
    'apps.feedback',

    # Email app
    'apps.email_app.apps.EmailAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auditlog.middleware.AuditlogMiddleware', # Adicionado para o django-auditlog
    "allauth.account.middleware.AccountMiddleware",
    "velzon.middleware.LockScreenMiddleware", # Middleware da tela de bloqueio
    "velzon.middleware.CacheControlMiddleware", # Middleware para controle de cache
]

ROOT_URLCONF = 'velzon.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Mantém a referência correta à pasta de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'velzon.context_processors.app_version_processor',
                'apps.configuracao.context_processors.configuracao_site',
            ],
        },
    },
]

WSGI_APPLICATION = 'velzon.wsgi.application'




AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]
AUTH_PASSWORD_VALIDATORS = []

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_L10N = True # Habilita a formatação de números e datas para a localidade
USE_TZ = True

# Arquivos Estáticos e Mídia
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Configuração do WhiteNoise para armazenamento de arquivos estáticos
# Isso permite que o WhiteNoise sirva arquivos estáticos comprimidos e com cache.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de terceiros (allauth, crispy, etc.)
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = "none"
# LOGIN_REDIRECT_URL é agora controlado pelo ACCOUNT_ADAPTER
ACCOUNT_ADAPTER = 'velzon.adapters.MyAccountAdapter'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5" # Adicionado para compatibilidade com Bootstrap 5
CRISPY_TEMPLATE_PACK = 'bootstrap5' # Alterado para Bootstrap 5
LOGIN_URL = '/account/login/'
ACCOUNT_FORMS = {
    'login': 'velzon.forms.UserLoginForm',
    'signup': 'velzon.forms.UserRegistrationForm',
    'change_password': 'velzon.forms.PasswordChangeForm',
    'set_password': 'velzon.forms.PasswordSetForm',
    'reset_password': 'velzon.forms.PasswordResetForm',
    'reset_password_from_key': 'velzon.forms.PasswordResetKeyForm',
}

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
# Configurações do Allauth para login com e-mail ou nome de usuário
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'padrao': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'padrao',
        },
    },
    # Qualquer logger sem configuração própria (warnings e erros) vai para o console.
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        # Sem isto, com DEBUG=False o Django manda o traceback de um erro 500 SÓ para
        # o AdminEmailHandler (o console padrão do Django exige DEBUG=True) -- e o erro
        # sumia do `docker compose logs web`. Agora sai sempre no console do container.
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # 404 de robôs procurando /.env, /.git etc. não precisa poluir o log.
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'velzon.adapters': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Falhas de comunicação com a API do SynDoc aparecem no `docker compose logs web`.
        'apps.tenants': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
