#!/usr/bin/env bash
# Replica num servidor Ubuntu NOVO a configuração do Apache coletada do servidor
# de origem pelo deploy/coletar_config.sh (proxy reverso, vhosts wildcard,
# módulos, certificados) e instala o Docker para subir o painel.
#
# Uso (no servidor novo, a partir da pasta do projeto, com deploy/origem/ presente):
#   sudo ./deploy/provisionar_servidor.sh [--certificados ARQUIVO.tar.gz] [--sem-docker]
#
#   --certificados ARQ  pacote gerado na origem com "coletar_config.sh --com-certificados"
#                       (certificados, chaves e contas do Let's Encrypt)
#   --sem-docker        não instala o Docker
#
# Pode ser executado mais de uma vez. Antes de alterar, salva /etc/apache2 em
# /root/apache2-antes-<data>.tar.gz. Sites cujo certificado ainda não existe
# ficam desabilitados e são listados no final. Não mexe em firewall, banco nem DNS.
set -euo pipefail

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; }

CERT_TAR=""
SEM_DOCKER=0
while [ $# -gt 0 ]; do
  case "$1" in
    --certificados) CERT_TAR="${2:-}"; [ -n "$CERT_TAR" ] || { echo "ERRO: --certificados exige um arquivo." >&2; exit 1; }; shift ;;
    --sem-docker) SEM_DOCKER=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opção desconhecida: $1" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

die() { echo "ERRO: $*" >&2; exit 1; }
AVISOS=()
aviso() { AVISOS+=("$*"); echo "    AVISO: $*" >&2; }

[ "$(id -u)" -eq 0 ] || die "execute com sudo."
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
SRC="$DIR/origem"
A=/etc/apache2
[ -f "$SRC/sites-enabled.txt" ] && [ -d "$SRC/apache2" ] \
  || die "$SRC não encontrado. Rode 'sudo ./deploy/coletar_config.sh' no servidor de origem e traga a pasta deploy/origem/."
[ -z "$CERT_TAR" ] || [ -f "$CERT_TAR" ] || die "pacote de certificados não encontrado: $CERT_TAR"
# shellcheck disable=SC1091
. /etc/os-release
[ "${ID:-}" = "ubuntu" ] || aviso "este script foi feito para Ubuntu (detectado: ${PRETTY_NAME:-desconhecido})."

export DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------------ pacotes ----
echo "==> Instalando Apache e utilitários..."
apt-get update -qq
apt-get install -y -qq apache2 openssl curl ca-certificates >/dev/null

if [ -s "$SRC/pacotes-modulos.txt" ]; then
  while read -r pkg; do
    [ -n "$pkg" ] || continue
    echo "    módulo extra: $pkg"
    apt-get install -y -qq "$pkg" >/dev/null 2>&1 \
      || aviso "pacote '$pkg' (módulo do Apache na origem) não está disponível neste Ubuntu; instale o equivalente."
  done < "$SRC/pacotes-modulos.txt"
fi

valor() { grep -E "^$1=" "$SRC/certbot.txt" 2>/dev/null | cut -d= -f2- || true; }
INSTALACAO="$(valor instalacao)"
AUTENTICADORES="$(valor autenticadores)"
case "$INSTALACAO" in
  snap)
    echo "==> Instalando o Certbot (snap, como na origem)..."
    command -v snap >/dev/null 2>&1 || apt-get install -y -qq snapd >/dev/null
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot
    for a in $AUTENTICADORES; do
      case "$a" in dns-*)
        snap set certbot trust-plugin-with-root=ok
        snap install "certbot-$a" || aviso "plugin do Certbot 'certbot-$a' não instalado."
      ;; esac
    done ;;
  apt|outra)
    echo "==> Instalando o Certbot (apt)..."
    [ "$INSTALACAO" = apt ] || aviso "o Certbot da origem não veio de apt nem snap; instalando por apt."
    apt-get install -y -qq certbot >/dev/null
    for a in $AUTENTICADORES; do
      case "$a" in
        apache|dns-*) apt-get install -y -qq "python3-certbot-$a" >/dev/null 2>&1 \
          || aviso "plugin do Certbot 'python3-certbot-$a' não instalado." ;;
      esac
    done ;;
esac

if [ "$SEM_DOCKER" -eq 0 ]; then
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "==> Docker já instalado."
  else
    echo "==> Instalando o Docker (repositório oficial)..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
  fi
  if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ]; then
    usermod -aG docker "$SUDO_USER"
  fi
fi

# ------------------------------------------------------------------- Apache ----
BACKUP="/root/apache2-antes-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "==> Backup da configuração atual em $BACKUP"
tar -czf "$BACKUP" -C /etc apache2

echo "==> Copiando a configuração da origem..."
cp -r "$SRC/apache2/." "$A/"
[ -d "$SRC/extras" ] && cp -r "$SRC/extras/." /

if [ -n "$CERT_TAR" ]; then
  echo "==> Restaurando certificados de $CERT_TAR"
  tar -xzpf "$CERT_TAR" -C /
fi

echo "==> Habilitando módulos..."
MPM="$(grep -E '^mpm_' "$SRC/mods-enabled.txt" | head -n1 || true)"
if [ -n "$MPM" ]; then
  for m in mpm_event mpm_worker mpm_prefork; do
    [ "$m" = "$MPM" ] || a2dismod -q -f "$m" >/dev/null 2>&1 || true
  done
fi
while read -r m; do
  [ -n "$m" ] || continue
  if [ -e "$A/mods-available/$m.load" ]; then
    a2enmod -q "$m" >/dev/null || aviso "não foi possível habilitar o módulo '$m'."
  else
    aviso "módulo '$m' habilitado na origem não existe neste servidor."
  fi
done < "$SRC/mods-enabled.txt"

echo "==> Habilitando confs..."
while read -r c; do
  [ -n "$c" ] || continue
  if [ -e "$A/conf-available/$c.conf" ]; then
    a2enconf -q "$c" >/dev/null || aviso "não foi possível habilitar a conf '$c'."
  else
    aviso "conf '$c' habilitada na origem não existe neste servidor."
  fi
done < "$SRC/conf-enabled.txt"

# Arquivos (certificados, chaves, includes) que um site cita e que não existem aqui.
faltando() {
  { grep -iE '^[[:space:]]*(SSLCertificateFile|SSLCertificateKeyFile|SSLCertificateChainFile|SSLCACertificateFile|Include)[[:space:]]+' "$1" || true; } \
    | awk '{print $2}' | tr -d "\"'" | sort -u | while read -r p; do
        case "$p" in /*) ;; *) p="$A/$p" ;; esac
        case "$p" in *[*?]*) continue ;; esac
        [ -e "$p" ] || echo "$p"
      done
}

echo "==> Habilitando sites..."
# Sites habilitados aqui que não estavam na origem (ex.: 000-default) saem.
for f in "$A/sites-enabled"/*.conf; do
  [ -e "$f" ] || [ -L "$f" ] || continue
  s="$(basename "$f" .conf)"
  grep -qxF "$s" "$SRC/sites-enabled.txt" || a2dissite -q "$s" >/dev/null || true
done
HABILITADOS=()
PENDENTES=()
while read -r s; do
  [ -n "$s" ] || continue
  conf="$A/sites-available/$s.conf"
  [ -e "$conf" ] || { aviso "site '$s' não encontrado em sites-available."; continue; }
  FALTA="$(faltando "$conf")"
  if [ -n "$FALTA" ]; then
    a2dissite -q "$s" >/dev/null 2>&1 || true
    PENDENTES+=("$s: $(echo "$FALTA" | tr '\n' ' ')")
  else
    a2ensite -q "$s" >/dev/null
    HABILITADOS+=("$s")
  fi
done < "$SRC/sites-enabled.txt"

echo "==> Validando a configuração (apache2ctl configtest)..."
if ! apache2ctl configtest; then
  die "configuração inválida; o Apache NÃO foi recarregado. Para voltar ao estado anterior: tar -xzf $BACKUP -C /etc"
fi
if [ -d /run/systemd/system ]; then
  systemctl enable apache2 >/dev/null 2>&1 || true
  systemctl restart apache2
else
  service apache2 restart
fi

# Destinos locais do proxy que ainda não têm nada escutando.
SEM_BACKEND=()
if [ "${#HABILITADOS[@]}" -gt 0 ]; then
  for porta in $(for s in "${HABILITADOS[@]}"; do cat "$A/sites-available/$s.conf"; done \
      | grep -vE '^[[:space:]]*#' \
      | grep -oE '(https?|wss?)://(127\.0\.0\.1|localhost):[0-9]+' | sed 's/.*://' | sort -un); do
    ss -tln 2>/dev/null | grep -qE "[:.]$porta[[:space:]]" || SEM_BACKEND+=("$porta")
  done
fi

# ------------------------------------------------------------------- resumo ----
echo
echo "================================ RESUMO ================================"
echo "Sites habilitados (${#HABILITADOS[@]}): ${HABILITADOS[*]:-nenhum}"
if [ "${#PENDENTES[@]}" -gt 0 ]; then
  echo
  echo "Sites NÃO habilitados -- faltam arquivos (certificado/chave/include):"
  printf '  - %s\n' "${PENDENTES[@]}"
  echo "  Traga os certificados da origem (coletar_config.sh --com-certificados) e rode"
  echo "  de novo com --certificados ARQUIVO, ou emita novos com o certbot (domínios e"
  echo "  método em deploy/origem/relatorio.txt e deploy/origem/letsencrypt-renewal/)"
  echo "  e rode este script novamente."
fi
if [ "${#SEM_BACKEND[@]}" -gt 0 ]; then
  echo
  echo "Portas locais usadas pelo proxy sem aplicação escutando ainda: ${SEM_BACKEND[*]}"
  echo "  (o Apache responde 503 nesses domínios até as aplicações subirem)"
fi
if [ "${#AVISOS[@]}" -gt 0 ]; then
  echo
  echo "Avisos:"
  printf '  - %s\n' "${AVISOS[@]}"
fi
echo
echo "Próximos passos:"
echo "  1. Painel: confira o .env na pasta do projeto e rode ./build.sh"
[ "$SEM_DOCKER" -eq 1 ] || [ -z "${SUDO_USER:-}" ] \
  || echo "     (saia e entre de novo na sessão para o usuário $SUDO_USER usar o docker sem sudo)"
echo "  2. Banco e demais aplicações do proxy (ex.: SynDoc): migrar à parte"
echo "  3. Firewall: compare com a seção 'Firewall (ufw)' de deploy/origem/relatorio.txt"
echo "  4. DNS: aponte os domínios para este servidor quando tudo responder"
echo "Backup da configuração anterior do Apache: $BACKUP"
