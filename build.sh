#!/usr/bin/env bash
# Atualiza o código e sobe o painel de assinaturas no Docker.
# Uso no servidor:  ./build.sh
set -euo pipefail

# Garante execução a partir do diretório do projeto (onde está este script).
cd "$(dirname "$(readlink -f "$0")")"

# Detecta o comando do Compose (plugin v2 "docker compose" ou legado "docker-compose").
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "ERRO: Docker Compose não encontrado. Instale o plugin 'docker compose'." >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "ERRO: .env não encontrado. Copie .env.example para .env e ajuste (SECRET_KEY, POSTGRES_*, SAAS_API_*)." >&2
  exit 1
fi

echo "==> Atualizando código (git pull)..."
git pull --ff-only

# Constrói a imagem ANTES de trocar o container: o painel antigo continua
# servindo durante o build (pip + npm/gulp levam alguns minutos).
echo "==> Construindo a imagem..."
$DC build web

# --force-recreate garante que o entrypoint rode a cada deploy -- é ele que cria
# o schema do painel (POSTGRES_SCHEMA), aplica as migrações (migrate), garante o
# superusuário inicial e coleta os estáticos antes do Gunicorn subir. Sem isso,
# um deploy só de .env ou sem mudança na imagem não recriaria o container.
echo "==> Subindo os containers (migrate roda no entrypoint)..."
$DC up -d --force-recreate --remove-orphans

echo "==> Limpando imagens antigas..."
docker image prune -f >/dev/null 2>&1 || true

# Aguarda o Gunicorn responder na porta publicada (APP_PORT do .env, padrão 8001).
# O entrypoint só sobe o Gunicorn depois de migrate/collectstatic, então a
# espera cobre essas etapas. /account/login/ é público e responde 200.
APP_PORT="$(grep -E '^APP_PORT=' .env | tail -n1 | cut -d= -f2- | tr -d '"'"'"' \r' || true)"
APP_PORT="${APP_PORT:-8001}"
echo "==> Aguardando o painel responder em http://localhost:${APP_PORT}/ ..."
for i in $(seq 1 60); do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: localhost' "http://localhost:${APP_PORT}/account/login/" || true)"
  case "$CODE" in
    200|301|302) echo "    OK (HTTP ${CODE})"; break ;;
  esac
  # Container reiniciando = o entrypoint falhou (banco, migrate...). Não adianta esperar.
  STATE="$(docker inspect -f '{{.State.Status}} {{.RestartCount}}' subscription_web 2>/dev/null || true)"
  case "$STATE" in
    restarting*|exited*)
      echo "ERRO: o container web não ficou de pé ($STATE). Últimas linhas do log:" >&2
      $DC logs --tail=40 web >&2
      exit 1 ;;
  esac
  if [ "$i" -eq 60 ]; then
    echo "AVISO: o painel não respondeu em 2 minutos. Últimas linhas do log:" >&2
    $DC logs --tail=40 web >&2
    $DC ps
    exit 1
  fi
  sleep 2
done

echo "==> Status:"
$DC ps
echo "==> Deploy concluído. Logs: $DC logs -f web"
