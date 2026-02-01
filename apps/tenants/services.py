import requests

from django.conf import settings


class SaasApiError(Exception):
    pass


class SaasApiClient:
    def __init__(self) -> None:
        self.base_url = getattr(settings, "SAAS_API_BASE_URL", None)
        self.api_key = getattr(settings, "SAAS_API_KEY", None)

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _get_url(self, path: str) -> str:
        if not self.base_url:
            raise SaasApiError("SAAS_API_BASE_URL não está configurada nas settings.")
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _handle_response(self, response: requests.Response, action: str):
        try:
            data = response.json()
        except ValueError:
            data = None

        if 200 <= response.status_code < 300:
            return data

        detail = None
        if isinstance(data, dict):
            detail = data.get("detail")

        message = f"{action} (status {response.status_code})"
        if detail:
            message = f"{message}: {detail}"
        raise SaasApiError(message)

    def list_tenants(self) -> list:
        try:
            url = self._get_url("api/tenants/")
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            data = self._handle_response(response, "Erro ao buscar tenants na API")
            if isinstance(data, list):
                return data
            return []
        except requests.RequestException as exc:
            raise SaasApiError(f"Erro ao buscar tenants na API: {exc}") from exc

    def retrieve_tenant(self, schema_name: str) -> dict:
        try:
            url = self._get_url(f"api/tenants/{schema_name}/")
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            data = self._handle_response(response, "Erro ao buscar tenant na API")
            if isinstance(data, dict):
                return data
            raise SaasApiError("Resposta inesperada da API ao buscar tenant.")
        except requests.RequestException as exc:
            raise SaasApiError(f"Erro ao buscar tenant na API: {exc}") from exc

    def create_tenant(self, payload: dict) -> dict:
        try:
            url = self._get_url("api/tenants/create/")
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
            data = self._handle_response(response, "Erro ao criar tenant na API")
            if isinstance(data, dict):
                return data
            return {}
        except requests.RequestException as exc:
            raise SaasApiError(f"Erro ao criar tenant na API: {exc}") from exc

    def update_tenant(self, schema_name: str, payload: dict, partial: bool = True) -> dict:
        try:
            url = self._get_url(f"api/tenants/{schema_name}/update/")
            method = requests.patch if partial else requests.put
            response = method(url, json=payload, headers=self._get_headers(), timeout=10)
            data = self._handle_response(response, "Erro ao atualizar tenant na API")
            if isinstance(data, dict):
                return data
            return {}
        except requests.RequestException as exc:
            raise SaasApiError(f"Erro ao atualizar tenant na API: {exc}") from exc
