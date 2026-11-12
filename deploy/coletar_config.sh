#!/usr/bin/env bash
# Coleta a configuração do Apache (proxy reverso, vhosts wildcard, módulos e
# certificados) do servidor de ORIGEM, para ser reaplicada em outro servidor
# pelo deploy/provisionar_servidor.sh.
#
# Uso (no servidor de origem, a partir da pasta do projeto):
#   sudo ./deploy/coletar_config.sh                      # só configuração (sem segredos)
#   sudo ./deploy/coletar_config.sh --com-certificados   # + pacote com certificados/chaves
#
# Só LÊ o servidor; nada é alterado. Gera:
#   deploy/origem/                        configuração e relatório (pode ir para o git)
#   deploy/certificados-origem.tar.gz     chaves privadas -- NUNCA vai para o git
#                                         (.gitignore); leve direto ao servidor novo por scp
set -euo pipefail

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

COM_CERTS=0
for arg in "$@"; do
  case "$arg" in
    --com-certificados) COM_CERTS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opção desconhecida: $arg" >&2; usage >&2; exit 1 ;;
  esac
done

[ "$(id -u)" -eq 0 ] || { echo "ERRO: execute com sudo." >&2; exit 1; }
command -v apache2ctl >/dev/null 2>&1 || { echo "ERRO: Apache (apache2ctl) não encontrado neste servidor." >&2; exit 1; }

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
OUT="$DIR/origem"
A=/etc/apache2

rm -rf "$OUT"
mkdir -p "$OUT/apache2/sites-available" "$OUT/apache2/conf-available"

echo "==> Copiando a configuração do Apache..."
for f in apache2.conf ports.conf envvars; do
  [ -f "$A/$f" ] && cp "$A/$f" "$OUT/apache2/"
done
cp -r "$A/sites-available/." "$OUT/apache2/sites-available/"
cp -r "$A/conf-available/." "$OUT/apache2/conf-available/"

# O que está habilitado (nomes sem extensão), para refazer com a2enmod/a2ensite/a2enconf.
listar() { find "$A/$1" -maxdepth 1 \( -type l -o -type f \) -name "*.$2" -printf '%f\n' | sed "s/\.$2\$//" | sort; }
listar mods-enabled load  > "$OUT/mods-enabled.txt"
listar sites-enabled conf > "$OUT/sites-enabled.txt"
listar conf-enabled conf  > "$OUT/conf-enabled.txt"

# Sites/confs habilitados que não vieram de *-available (arquivo solto ou link
# para fora): copia o conteúdo para o *-available do pacote.
for tipo in sites conf; do
  for f in "$A/$tipo-enabled"/*.conf; do
    [ -e "$f" ] || continue
    dest="$OUT/apache2/$tipo-available/$(basename "$f")"
    [ -e "$dest" ] || cp -L "$f" "$dest"
  done
done

# Confs de módulos alteradas em relação ao pacote (ex.: ssl.conf, mpm_*.conf).
dpkg -V apache2 2>/dev/null | awk '$2=="c" && $3 ~ /mods-available\/.*\.conf$/ {print $3}' | while read -r f; do
  mkdir -p "$OUT/apache2/mods-available"
  cp "$f" "$OUT/apache2/mods-available/"
done

# Pacotes extras que fornecem módulos habilitados (ex.: libapache2-mod-php).
while read -r m; do
  dpkg -S "$A/mods-available/$m.load" 2>/dev/null | cut -d: -f1 || true
done < "$OUT/mods-enabled.txt" | sort -u | grep -vx apache2 > "$OUT/pacotes-modulos.txt" || true

# Caminhos citados por uma diretiva nas configurações copiadas (um por linha).
refs() {
  grep -rhiE "^[[:space:]]*($1)[[:space:]]+" "$OUT/apache2" 2>/dev/null \
    | awk '{print $2}' | tr -d "\"'" | sort -u || true
}

# Arquivos incluídos que ficam fora das pastas já copiadas
# (ex.: /etc/letsencrypt/options-ssl-apache.conf, /etc/apache2/snippets/x.conf).
refs 'Include|IncludeOptional' | while read -r p; do
  case "$p" in /*) ;; *) p="$A/$p" ;; esac
  case "$p" in "$A"/*-enabled/*|"$A/ports.conf") continue ;; esac
  for f in $p; do   # expande curingas
    [ -f "$f" ] || continue
    grep -q 'PRIVATE KEY' "$f" 2>/dev/null && continue
    case "$f" in
      "$A"/*) dest="$OUT/apache2/${f#"$A"/}" ;;
      *)      dest="$OUT/extras$f" ;;
    esac
    [ -e "$dest" ] && continue
    mkdir -p "$(dirname "$dest")"
    cp -L "$f" "$dest"
  done
done

echo "==> Levantando certificados..."
CERTS="$(refs 'SSLCertificateFile')"
ARQS_TLS="$(refs 'SSLCertificateFile|SSLCertificateKeyFile|SSLCertificateChainFile|SSLCACertificateFile')"

# Certbot: como foi instalado e quais autenticadores as renovações usam.
INSTALACAO=nenhuma
if command -v certbot >/dev/null 2>&1; then
  if command -v snap >/dev/null 2>&1 && snap list certbot >/dev/null 2>&1; then
    INSTALACAO=snap
  elif dpkg -s certbot >/dev/null 2>&1; then
    INSTALACAO=apt
  else
    INSTALACAO=outra
  fi
fi
AUTENTICADORES=""
CREDENCIAIS=""
if [ -d /etc/letsencrypt/renewal ]; then
  mkdir -p "$OUT/letsencrypt-renewal"
  cp /etc/letsencrypt/renewal/*.conf "$OUT/letsencrypt-renewal/" 2>/dev/null || true
  AUTENTICADORES="$(grep -hE '^authenticator[[:space:]]*=' /etc/letsencrypt/renewal/*.conf 2>/dev/null \
    | sed 's/.*=[[:space:]]*//' | sort -u | tr '\n' ' ' || true)"
  CREDENCIAIS="$(grep -hE '^dns_[a-z0-9_]*credentials[[:space:]]*=' /etc/letsencrypt/renewal/*.conf 2>/dev/null \
    | sed 's/.*=[[:space:]]*//' | sort -u || true)"
fi
{
  echo "instalacao=$INSTALACAO"
  echo "autenticadores=${AUTENTICADORES% }"
} > "$OUT/certbot.txt"

echo "==> Gerando o relatório..."
REL="$OUT/relatorio.txt"
sec() {  # sec "Título" comando...
  { echo; echo "===== $1 ====="; "${@:2}" 2>&1 || echo "(indisponível)"; } >> "$REL"
}
{
  echo "Configuração coletada em $(date '+%d/%m/%Y %H:%M') -- servidor $(hostname)"
  # shellcheck disable=SC1091
  . /etc/os-release && echo "Sistema: $PRETTY_NAME"
} > "$REL"
sec "Apache: versão" apache2ctl -v
sec "Apache: vhosts (apache2ctl -S)" apache2ctl -S
sec "Apache: módulos carregados" apache2ctl -M
sec "Sites habilitados" cat "$OUT/sites-enabled.txt"
sec "Proxy reverso (sites habilitados)" grep -rnEi \
  '^[[:space:]]*(<VirtualHost|ServerName|ServerAlias|ProxyPass|ProxyPassMatch|ProxyPassReverse|ProxyPreserveHost|RequestHeader|RewriteRule|SSLCertificate)' \
  "$A/sites-enabled/"
{
  echo; echo "===== Certificados usados pelo Apache ====="
  for c in $CERTS; do
    echo "--- $c"
    if [ -e "$c" ]; then
      openssl x509 -in "$c" -noout -subject -issuer -enddate -ext subjectAltName 2>&1 || true
    else
      echo "(arquivo não existe)"
    fi
  done
} >> "$REL"
sec "Certbot: instalação e autenticadores" cat "$OUT/certbot.txt"
sec "Certbot: certificados" certbot certificates
sec "Certbot: renovação automática (timers)" systemctl list-timers --all --no-pager '*certbot*'
sec "Certbot: renovação automática (cron)" grep -rs certbot /etc/crontab /etc/cron.d /var/spool/cron/crontabs
sec "Firewall (ufw)" ufw status verbose
sec "Portas em escuta" ss -tlnp
sec "Docker: containers" docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
sec "Docker: redes" docker network ls
sec "PostgreSQL" pg_lsclusters
sec "/etc/hosts" cat /etc/hosts

if [ "$COM_CERTS" -eq 1 ]; then
  echo "==> Empacotando certificados e chaves privadas..."
  LISTA="$(mktemp)"
  [ -d /etc/letsencrypt ] && echo "etc/letsencrypt" >> "$LISTA"
  for f in $ARQS_TLS $CREDENCIAIS; do
    # letsencrypt já entra inteiro; o snakeoil é gerado pelo próprio Ubuntu.
    case "$f" in /etc/letsencrypt/*|*/ssl-cert-snakeoil.*) continue ;; /*) ;; *) f="$A/$f" ;; esac
    [ -e "$f" ] && echo "${f#/}" >> "$LISTA"
  done
  PACOTE="$DIR/certificados-origem.tar.gz"
  if [ -s "$LISTA" ]; then
    ( umask 077; tar -czf "$PACOTE" -C / -T "$LISTA" )
    chmod 600 "$PACOTE"
  else
    echo "    Nenhum certificado encontrado para empacotar."
    PACOTE=""
  fi
  rm -f "$LISTA"
fi

# Devolve os arquivos a quem chamou o sudo (para git add / scp sem root).
if [ -n "${SUDO_USER:-}" ]; then
  chown -R "$SUDO_USER": "$OUT"
  [ -n "${PACOTE:-}" ] && chown "$SUDO_USER": "$PACOTE"
fi

echo
echo "Pronto."
echo "  Configuração: $OUT"
echo "  Relatório:    $REL"
if [ -n "${PACOTE:-}" ]; then
  echo "  Certificados: $PACOTE  (contém chaves privadas; não versionar)"
  echo
  echo "Leve o pacote ao servidor novo, por exemplo:"
  echo "  scp $PACOTE usuario@servidor-novo:~/"
fi
echo
echo "Próximo passo: levar deploy/origem/ ao servidor novo (git ou scp) e rodar"
echo "  sudo ./deploy/provisionar_servidor.sh --certificados ~/certificados-origem.tar.gz"
