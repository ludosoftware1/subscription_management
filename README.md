# Painel de assinaturas (subscription_management)

Painel administrativo que **gerencia os clientes (tenants) do UltraDoc**: criação de tenant
com superusuário, plano (licenças, armazenamento, valor mensal), vigência (pago até / período de
teste), domínio de acesso e registro de pagamentos.

Ele **não acessa o banco do UltraDoc**. Toda a gestão passa pela API `/api/tenants/` do UltraDoc
(`apps/users/api_views.py` naquele projeto), autenticada pelo cabeçalho `X-API-Key`. Só os
pagamentos (`apps.tenants.TenantPayment`) e os usuários deste painel ficam no banco próprio.

```
navegador ──► subscription_web (Django/Gunicorn, :8001)
                    │  X-API-Key + Host: admin.ultradoc.com.br
                    ▼
              syndoc_web (UltraDoc, :8010) ──► GET/POST/PATCH /api/tenants/...
```

## Produção (Docker)

Tudo roda em Docker, no mesmo servidor do UltraDoc. O Postgres fica no host (fora do Docker),
como no UltraDoc, mas num **banco separado**.

### 1. No UltraDoc (uma vez)

1. No `.env` do UltraDoc:
   - `SAAS_API_KEY` — chave longa e aleatória (32+ caracteres; `openssl rand -hex 32`).
   - `SAAS_API_HOSTS=admin.ultradoc.com.br` — host administrativo onde a API responde.
   - inclua esse host em `ALLOWED_HOSTS` (e em `CSRF_TRUSTED_ORIGINS`, se for acessá-lo pelo navegador).
2. Cadastre o host administrativo como domínio da plataforma (schema `public`):
   ```bash
   docker compose exec web python manage.py create_platform_domain admin.ultradoc.com.br
   ```
   Sem isso o `django-tenants` responde 404 para o host ("No tenant for hostname").
3. `docker compose up -d web` para recarregar o `.env`.

### 2. Neste painel

```bash
cp .env.example .env     # ajuste SECRET_KEY, POSTGRES_*, SAAS_API_*, superusuário
sudo -u postgres createdb --owner=ultradoc subscription_management
docker compose up -d --build
docker compose logs -f web
```

Variáveis que ligam os dois sistemas (`.env` deste painel):

| Variável | Valor típico | Observação |
|---|---|---|
| `SAAS_API_BASE_URL` | `http://host.docker.internal:8010` | porta publicada pelo compose do UltraDoc (`APP_PORT` de lá). Pode ser a URL pública (`https://admin.ultradoc.com.br`). |
| `SAAS_API_KEY` | igual ao do UltraDoc | |
| `SAAS_API_HOST_HEADER` | `admin.ultradoc.com.br` | enviado como `Host` nas chamadas internas; precisa estar em `SAAS_API_HOSTS`/`ALLOWED_HOSTS` do UltraDoc e ter o `Domain` criado acima. |
| `SAAS_API_FORWARDED_PROTO` | `https` | só se o UltraDoc roda com `SECURE_SSL_REDIRECT=True` e a chamada interna é por `http`. |
| `SAAS_API_CREATE_TIMEOUT` | `300` | criar tenant roda todas as migrations do schema novo. |
| `GUNICORN_TIMEOUT` | `360` | **maior** que `SAAS_API_CREATE_TIMEOUT`, senão o worker é morto no meio da criação. |

O painel inicial mostra se a conexão com o UltraDoc está funcionando e, em caso de erro, o que
conferir. Para falar com o UltraDoc pela rede interna do Docker em vez da porta publicada, veja o
bloco `networks` comentado em `docker-compose.yml`.

### Atualizar (deploy)

```bash
chmod +x build.sh   # uma vez
./build.sh
```

O `build.sh` faz `git pull`, constrói a imagem enquanto o container antigo continua no ar, recria
os containers, limpa imagens antigas e espera o painel responder na `APP_PORT`. Equivale a
`git pull && docker compose up -d --build`.

### Comandos úteis

```bash
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
```

## Desenvolvimento local

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # DEBUG=True; sem POSTGRES_*/DATABASE_URL usa SQLite
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Com o UltraDoc rodando localmente (`tenant1.localhost:8000`), use
`SAAS_API_BASE_URL=http://127.0.0.1:8000` e `SAAS_API_HOST_HEADER=tenant1.localhost`
(em desenvolvimento o UltraDoc aceita a API em qualquer domínio de tenant quando
`SAAS_API_HOSTS` está vazio).

Testes: `python manage.py test apps.tenants`.

## Estrutura

- `apps/tenants/` — telas de clientes e pagamentos; `services.py` é o cliente da API do
  UltraDoc; `utils.py` calcula a situação (ativo, em teste, vence em breve, vencido, sem
  vencimento) com a mesma regra do `TenantExpirationMiddleware` do UltraDoc.
- `apps/configuracao/`, `apps/email_app/`, `apps/perfil/`, `pages/` — configurações do site,
  e-mail de recuperação de senha, perfil e trilha de auditoria.
- `velzon/` — projeto Django (settings `development`/`production`), tema Velzon
  (<https://themesbrand.com/velzon/docs/django/getting-started.html>).

## Limitações conhecidas

- A API do UltraDoc não expõe exclusão de tenant; para desativar um cliente, defina "Pago até"
  no passado (o UltraDoc bloqueia o acesso) ou remova o tenant pelo próprio UltraDoc.
- A API do UltraDoc limita a 20 requisições por minuto por IP; as telas usam uma chamada de
  listagem por página para ficar dentro do limite.
