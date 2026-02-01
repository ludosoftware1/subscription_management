#!/usr/bin/env bash
# Exit on error
set -o errexit

# Define a variável de ambiente APP_VERSION com o último tag do Git
# export APP_VERSION=$(git describe --tags --abbrev=0)

# 1. Instala todas as dependências listadas no requirements.txt
pip install -r requirements.txt

# 2. Aplica as migrações do banco de dados
# python manage.py migrate

# 3. Coleta todos os arquivos estáticos para o diretório STATIC_ROOT
python manage.py collectstatic --no-input
