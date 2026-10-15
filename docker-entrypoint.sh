#!/bin/sh
# Ponto de entrada do container do painel de assinaturas.
# A cada inicialização: migrações, superusuário inicial (opcional), estáticos e Gunicorn.
set -e

echo "==> Conferindo o banco de dados..."
# Cria o schema do painel (POSTGRES_SCHEMA) e aborta se o destino for o schema
# public do SynDoc -- ver apps/core/management/commands/verificar_banco.py.
python manage.py verificar_banco

# Roda em TODA subida do container (o build.sh recria o container a cada deploy).
# Se falhar, o set -e para aqui e o Gunicorn não sobe com o banco desatualizado.
echo "==> Aplicando migrações..."
python manage.py migrate --noinput
python manage.py showmigrations --plan | grep -c '\[X\]' | xargs -I{} echo "    {} migrations aplicadas."

# Cria o superusuário só quando DJANGO_SUPERUSER_EMAIL e DJANGO_SUPERUSER_PASSWORD
# estão no .env. O login é por e-mail (allauth), então o username recebe o e-mail.
if [ -n "${DJANGO_SUPERUSER_EMAIL}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
  echo "==> Garantindo superusuário ${DJANGO_SUPERUSER_EMAIL}..."
  python manage.py createsuperuser --noinput \
    --username "${DJANGO_SUPERUSER_USERNAME:-$DJANGO_SUPERUSER_EMAIL}" \
    --email "${DJANGO_SUPERUSER_EMAIL}" 2>/dev/null \
    || echo "    (superusuário já existe; nada a fazer)"
fi

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# O timeout do Gunicorn precisa cobrir a criação de tenant no SynDoc
# (SAAS_API_CREATE_TIMEOUT, padrão 300s): a view fica bloqueada esperando a API
# rodar CREATE SCHEMA + migrations. Com o padrão de 30s o worker era morto no meio
# e o navegador recebia 502 mesmo com o tenant sendo criado do outro lado.
TIMEOUT="${GUNICORN_TIMEOUT:-360}"
echo "==> Iniciando Gunicorn na porta ${PORT:-8000} (timeout ${TIMEOUT}s)..."
exec gunicorn velzon.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --worker-class gthread \
  --timeout "${TIMEOUT}" \
  --access-logfile - \
  --error-logfile -
