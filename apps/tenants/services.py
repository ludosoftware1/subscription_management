"""Cliente HTTP da API de clientes do UltraDoc (``/api/tenants/``).

O UltraDoc expõe quatro endpoints autenticados pelo cabeçalho ``X-API-Key``
(``apps/users/api_views.py`` no projeto ultradoc):

- ``GET  api/tenants/``                        lista os clientes
- ``GET  api/tenants/<schema>/``               detalhe de um cliente
- ``POST api/tenants/create/``                 cria tenant + superusuário
- ``PATCH/PUT api/tenants/<schema>/update/``   atualiza plano/domínio

Observações de produção (tudo roda em Docker):

- Com ``django-tenants`` o UltraDoc resolve o tenant pelo ``Host`` da
  requisição, e a API só responde nos hosts de ``SAAS_API_HOSTS``. Quando o
  painel chama o UltraDoc pela rede interna (``http://host.docker.internal:8010``
  ou ``http://syndoc_web:8000``), ``SAAS_API_HOST_HEADER`` define o ``Host``
  enviado (o domínio administrativo cadastrado no UltraDoc).
- A criação de tenant roda ``CREATE SCHEMA`` + todas as migrations e pode levar
  minutos: ``SAAS_API_CREATE_TIMEOUT`` precisa ser menor que o timeout do
  Gunicorn deste painel (ver ``docker-entrypoint.sh``).
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SaasApiError(Exception):
    """Falha de comunicação ou de negócio ao falar com a API do UltraDoc."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class SaasApiNotConfigured(SaasApiError):
    """``SAAS_API_BASE_URL``/``SAAS_API_KEY`` não configuradas."""


class SaasApiTimeout(SaasApiError):
    """A API não respondeu a tempo. A operação PODE ter sido concluída do outro lado."""


class SaasApiClient:
    def __init__(self) -> None:
        self.base_url = getattr(settings, "SAAS_API_BASE_URL", None) or None
        self.api_key = getattr(settings, "SAAS_API_KEY", None) or None
        self.host_header = getattr(settings, "SAAS_API_HOST_HEADER", None) or None
        self.forwarded_proto = getattr(settings, "SAAS_API_FORWARDED_PROTO", None) or None
        self.timeout = int(getattr(settings, "SAAS_API_TIMEOUT", 15) or 15)
        self.create_timeout = int(getattr(settings, "SAAS_API_CREATE_TIMEOUT", 300) or 300)
        self.verify_ssl = bool(getattr(settings, "SAAS_API_VERIFY_SSL", True))

    # ------------------------------------------------------------------ infra
    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _get_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "subscription-management/1.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.host_header:
            headers["Host"] = self.host_header
        if self.forwarded_proto:
            headers["X-Forwarded-Proto"] = self.forwarded_proto
        return headers

    def _get_url(self, path: str) -> str:
        if not self.base_url:
            raise SaasApiNotConfigured(
                "SAAS_API_BASE_URL não está configurada. Informe a URL do UltraDoc no .env."
            )
        if not self.api_key:
            raise SaasApiNotConfigured(
                "SAAS_API_KEY não está configurada. Use a mesma chave definida no .env do UltraDoc."
            )
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _extract_detail(data):
        if isinstance(data, dict):
            for key in ("detail", "error", "message"):
                value = data.get(key)
                if value:
                    return str(value)
        return None

    def _handle_response(self, response: requests.Response, action: str):
        try:
            data = response.json()
        except ValueError:
            data = None

        status = response.status_code
        if 200 <= status < 300:
            return data

        detail = self._extract_detail(data)
        if detail is None:
            if status in (301, 302, 307, 308):
                detail = (
                    f"a API redirecionou para {response.headers.get('Location', '?')}. "
                    "Se o UltraDoc usa SECURE_SSL_REDIRECT, chame-o por HTTPS ou defina "
                    "SAAS_API_FORWARDED_PROTO=https para chamadas internas."
                )
            elif status == 401:
                detail = "chave de API inválida (SAAS_API_KEY diferente da configurada no UltraDoc)."
            elif status == 404:
                detail = (
                    "endpoint não encontrado. Confira SAAS_API_BASE_URL e se o host usado "
                    "(SAAS_API_HOST_HEADER) está em SAAS_API_HOSTS e cadastrado como domínio no UltraDoc."
                )
            elif status == 429:
                detail = "limite de requisições da API atingido. Aguarde um instante e tente novamente."
            elif status >= 500:
                detail = "erro interno no UltraDoc. Verifique os logs do container web do UltraDoc."

        message = f"{action} (HTTP {status})"
        if detail:
            message = f"{message}: {detail}"
        logger.warning("SaaS API: %s", message)
        raise SaasApiError(message, status_code=status)

    def _request(self, method: str, path: str, action: str, *, json=None, timeout=None):
        url = self._get_url(path)
        timeout = timeout or self.timeout
        try:
            response = requests.request(
                method,
                url,
                json=json,
                headers=self._get_headers(),
                timeout=timeout,
                verify=self.verify_ssl,
                allow_redirects=False,
            )
        except requests.Timeout as exc:
            logger.warning("SaaS API: timeout (%ss) em %s %s", timeout, method, url)
            raise SaasApiTimeout(
                f"{action}: o UltraDoc não respondeu em {timeout} segundos."
            ) from exc
        except requests.ConnectionError as exc:
            logger.warning("SaaS API: falha de conexão em %s %s: %s", method, url, exc)
            raise SaasApiError(
                f"{action}: não foi possível conectar ao UltraDoc em {self.base_url}. "
                "Confira SAAS_API_BASE_URL e se o container do UltraDoc está no ar."
            ) from exc
        except requests.RequestException as exc:
            logger.warning("SaaS API: erro em %s %s: %s", method, url, exc)
            raise SaasApiError(f"{action}: {exc}") from exc
        return self._handle_response(response, action)

    # -------------------------------------------------------------- endpoints
    def list_tenants(self) -> list:
        data = self._request("GET", "api/tenants/", "Erro ao buscar clientes na API")
        return data if isinstance(data, list) else []

    def retrieve_tenant(self, schema_name: str) -> dict:
        data = self._request("GET", f"api/tenants/{schema_name}/", "Erro ao buscar cliente na API")
        if isinstance(data, dict):
            return data
        raise SaasApiError("Resposta inesperada da API ao buscar cliente.")

    def create_tenant(self, payload: dict) -> dict:
        data = self._request(
            "POST",
            "api/tenants/create/",
            "Erro ao criar cliente na API",
            json=payload,
            timeout=self.create_timeout,
        )
        return data if isinstance(data, dict) else {}

    def update_tenant(self, schema_name: str, payload: dict, partial: bool = True) -> dict:
        data = self._request(
            "PATCH" if partial else "PUT",
            f"api/tenants/{schema_name}/update/",
            "Erro ao atualizar cliente na API",
            json=payload,
        )
        return data if isinstance(data, dict) else {}

    # ----------------------------------------------------------------- helpers
    def tenant_choices(self) -> list:
        """Pares ``(schema_name, rótulo)`` para selects de cliente."""
        return [
            (t.get("schema_name"), f'{t.get("client_name") or t.get("schema_name")} ({t.get("schema_name")})')
            for t in self.list_tenants()
            if t.get("schema_name")
        ]
