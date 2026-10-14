FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libcairo/pango/jpeg: weasyprint e pillow. nodejs/npm: build dos assets do tema (gulp).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2 \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python em camada própria (só reinstala quando requirements.txt muda).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Assets do tema: o gulp gera ./static a partir de ./src. Camada separada para
# não refazer o npm install a cada mudança em código Python/templates.
COPY package.json package-lock.json gulpfile.js ./
RUN npm install --no-audit --no-fund
COPY src ./src
RUN npx gulp build

# Código da aplicação (ver .dockerignore: sem .env, venv, node_modules, static/, media/).
COPY . .

ENV DJANGO_SETTINGS_MODULE=velzon.settings.production \
    PORT=8000

EXPOSE 8000

# Migrações, superusuário inicial, collectstatic e Gunicorn (timeout compatível
# com a criação de tenant no UltraDoc) ficam no entrypoint.
CMD ["sh", "docker-entrypoint.sh"]
