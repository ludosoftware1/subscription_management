"""Testes do app de clientes (tenants) -- rodam com SQLite:

    set DATABASE_URL=sqlite://:memory:
    python manage.py test apps.tenants
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import TenantForm
from .models import TenantPayment
from .services import SaasApiClient, SaasApiError, SaasApiNotConfigured, SaasApiTimeout
from .utils import compute_status, enrich_tenant, summarize_tenants

TODAY = date(2026, 10, 14)

API_SETTINGS = {
    "SAAS_API_BASE_URL": "http://ultradoc.test:8000",
    "SAAS_API_KEY": "k" * 40,
    "SAAS_API_HOST_HEADER": "admin.ultradoc.test",
    "SAAS_API_FORWARDED_PROTO": "https",
}


def _tenant(**overrides):
    base = {
        "schema_name": "cliente_a",
        "client_name": "Cliente A",
        "paid_until": "2026-12-31",
        "on_trial": False,
        "created_on": "2026-01-10",
        "monthly_price": "199.90",
        "manager_licenses": 2,
        "staff_licenses": 10,
        "storage_gb": 100,
        "storage_used_gb": 25.5,
        "storage_used_percent": 25.5,
        "primary_domain": "a.ultradoc.test",
        "domains": [],
    }
    base.update(overrides)
    return base


def _response(status=200, json_data=None, headers=None):
    response = mock.Mock(spec=requests.Response)
    response.status_code = status
    response.headers = headers or {}
    if json_data is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = json_data
    return response


# ---------------------------------------------------------------- utils ----
class StatusTests(TestCase):
    def test_vencido_tem_prioridade_mesmo_em_teste(self):
        tenant = _tenant(paid_until="2026-10-13", on_trial=True)
        self.assertEqual(compute_status(tenant, TODAY), "expired")

    def test_em_teste(self):
        self.assertEqual(compute_status(_tenant(on_trial=True), TODAY), "trial")

    def test_sem_vencimento(self):
        self.assertEqual(compute_status(_tenant(paid_until=None), TODAY), "no_due_date")

    def test_vence_em_breve_e_ativo(self):
        self.assertEqual(compute_status(_tenant(paid_until="2026-10-20"), TODAY), "expiring")
        self.assertEqual(compute_status(_tenant(paid_until="2026-10-22"), TODAY), "active")

    def test_enrich_converte_tipos(self):
        tenant = enrich_tenant(_tenant(), TODAY)
        self.assertEqual(tenant["paid_until"], date(2026, 12, 31))
        self.assertEqual(tenant["created_on"], date(2026, 1, 10))
        self.assertEqual(tenant["monthly_price"], Decimal("199.90"))
        self.assertEqual(tenant["status_label"], "Ativo")
        self.assertEqual(tenant["days_left"], 78)

    def test_summary_exclui_vencidos_da_receita(self):
        tenants = [
            enrich_tenant(_tenant(), TODAY),
            enrich_tenant(_tenant(schema_name="b", paid_until="2026-01-01", monthly_price="50"), TODAY),
        ]
        summary = summarize_tenants(tenants)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["expired"], 1)
        self.assertEqual(summary["mrr"], Decimal("199.90"))
        self.assertEqual(summary["storage_gb"], 200)
        self.assertEqual(summary["storage_percent"], 25.5)


# ---------------------------------------------------------------- forms ----
class TenantFormTests(TestCase):
    def _data(self, **overrides):
        data = {
            "schema_name": "prefeitura_xyz",
            "client_name": "Prefeitura XYZ",
            "email": "admin@xyz.gov.br",
            "password": "SenhaForte123",
            "primary_domain": "xyz.ultradoc.test",
            "manager_licenses": 1,
            "staff_licenses": 5,
            "storage_gb": 50,
            "monthly_price": "100.00",
        }
        data.update(overrides)
        return data

    def test_valido_normaliza_dominio(self):
        form = TenantForm(self._data(primary_domain="HTTPS://Xyz.UltraDoc.test:443/"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["primary_domain"], "xyz.ultradoc.test")

    def test_schema_invalido(self):
        for bad in ("pref-xyz", "1abc", "public", "pg_x", "pref xyz"):
            form = TenantForm(self._data(schema_name=bad))
            self.assertFalse(form.is_valid(), bad)
            self.assertIn("schema_name", form.errors, bad)

    def test_schema_normaliza_para_minusculas(self):
        form = TenantForm(self._data(schema_name=" Prefeitura_XYZ "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["schema_name"], "prefeitura_xyz")

    def test_senha_obrigatoria_na_criacao(self):
        form = TenantForm(self._data(password=""))
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_update_dispensa_credenciais(self):
        data = self._data(password="", email="")
        form = TenantForm(data, is_update=True)
        self.assertTrue(form.is_valid(), form.errors)


# ------------------------------------------------------------- services ----
@override_settings(**API_SETTINGS)
class SaasApiClientTests(TestCase):
    def test_nao_configurado(self):
        with override_settings(SAAS_API_BASE_URL=None):
            with self.assertRaises(SaasApiNotConfigured):
                SaasApiClient().list_tenants()

    @mock.patch("apps.tenants.services.requests.request")
    def test_headers_e_url(self, request):
        request.return_value = _response(200, [_tenant()])
        tenants = SaasApiClient().list_tenants()
        self.assertEqual(len(tenants), 1)
        args, kwargs = request.call_args
        self.assertEqual(args, ("GET", "http://ultradoc.test:8000/api/tenants/"))
        self.assertEqual(kwargs["headers"]["X-API-Key"], "k" * 40)
        self.assertEqual(kwargs["headers"]["Host"], "admin.ultradoc.test")
        self.assertEqual(kwargs["headers"]["X-Forwarded-Proto"], "https")
        self.assertFalse(kwargs["allow_redirects"])

    @mock.patch("apps.tenants.services.requests.request")
    def test_create_usa_timeout_longo(self, request):
        request.return_value = _response(201, {"schema_name": "x"})
        with override_settings(SAAS_API_CREATE_TIMEOUT=321):
            SaasApiClient().create_tenant({"schema_name": "x"})
        self.assertEqual(request.call_args.kwargs["timeout"], 321)
        self.assertEqual(request.call_args.args[0], "POST")

    @mock.patch("apps.tenants.services.requests.request")
    def test_erro_com_detail(self, request):
        request.return_value = _response(400, {"detail": "Já existe um domínio"})
        with self.assertRaises(SaasApiError) as ctx:
            SaasApiClient().retrieve_tenant("x")
        self.assertIn("Já existe um domínio", str(ctx.exception))
        self.assertEqual(ctx.exception.status_code, 400)

    @mock.patch("apps.tenants.services.requests.request")
    def test_mensagens_por_status(self, request):
        for status, trecho in ((401, "chave de API"), (404, "endpoint"), (429, "limite"), (500, "erro interno")):
            request.return_value = _response(status)
            with self.assertRaises(SaasApiError) as ctx:
                SaasApiClient().list_tenants()
            self.assertIn(trecho, str(ctx.exception), status)

    @mock.patch("apps.tenants.services.requests.request")
    def test_redirect_explica_ssl(self, request):
        request.return_value = _response(301, headers={"Location": "https://admin.ultradoc.test/api/tenants/"})
        with self.assertRaises(SaasApiError) as ctx:
            SaasApiClient().list_tenants()
        self.assertIn("SECURE_SSL_REDIRECT", str(ctx.exception))

    @mock.patch("apps.tenants.services.requests.request", side_effect=requests.Timeout())
    def test_timeout(self, request):
        with self.assertRaises(SaasApiTimeout):
            SaasApiClient().create_tenant({})

    @mock.patch("apps.tenants.services.requests.request", side_effect=requests.ConnectionError())
    def test_conexao(self, request):
        with self.assertRaises(SaasApiError) as ctx:
            SaasApiClient().list_tenants()
        self.assertIn("não foi possível conectar", str(ctx.exception))


# ---------------------------------------------------------------- views ----
@override_settings(**API_SETTINGS)
class ViewTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("admin", "admin@x.com", "x")
        self.client.force_login(user)

    def test_exige_login(self):
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/account/login/", response["Location"])

    @mock.patch("apps.tenants.views.SaasApiClient.list_tenants")
    def test_dashboard(self, list_tenants):
        list_tenants.return_value = [
            _tenant(),
            _tenant(schema_name="vencido", client_name="Vencido", paid_until="2020-01-01"),
        ]
        TenantPayment.objects.create(
            schema_name="cliente_a", client_name="Cliente A", amount="199.90",
            payment_date=date.today(), status=TenantPayment.STATUS_PAID,
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["api_ok"])
        self.assertEqual(response.context["summary"]["expired"], 1)
        self.assertEqual([t["schema_name"] for t in response.context["attention"]], ["vencido"])
        self.assertContains(response, "UltraDoc conectado")

    @mock.patch("apps.tenants.views.SaasApiClient.list_tenants", side_effect=SaasApiError("API fora do ar"))
    def test_dashboard_sem_api(self, list_tenants):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["api_ok"])
        self.assertContains(response, "API fora do ar")

    @mock.patch("apps.tenants.views.SaasApiClient.list_tenants")
    def test_lista_com_filtros(self, list_tenants):
        list_tenants.return_value = [
            _tenant(),
            _tenant(schema_name="teste", client_name="Em Teste", on_trial=True, primary_domain="t.ultradoc.test"),
        ]
        response = self.client.get(reverse("tenants:list"), {"status": "trial"})
        self.assertEqual([t["schema_name"] for t in response.context["tenants"]], ["teste"])
        response = self.client.get(reverse("tenants:list"), {"q": "a.ultradoc"})
        self.assertEqual([t["schema_name"] for t in response.context["tenants"]], ["cliente_a"])

    @mock.patch("apps.tenants.views.SaasApiClient.create_tenant")
    def test_criacao(self, create_tenant):
        create_tenant.return_value = {"schema_name": "novo", "client_name": "Novo", "superuser_email": "admin@novo.gov.br"}
        response = self.client.post(
            reverse("tenants:create"),
            {
                "schema_name": "novo",
                "client_name": "Novo",
                "email": "admin@novo.gov.br",
                "password": "SenhaForte123",
                "primary_domain": "novo.ultradoc.test",
                "monthly_price": "10.00",
                "manager_licenses": 1,
                "staff_licenses": 2,
                "storage_gb": 3,
                "on_trial": "on",
                "paid_until": "2027-01-31",
            },
        )
        self.assertRedirects(response, reverse("tenants:detail", args=["novo"]), fetch_redirect_response=False)
        payload = create_tenant.call_args.args[0]
        self.assertEqual(payload["domain"], "novo.ultradoc.test")
        self.assertEqual(payload["paid_until"], "2027-01-31")
        self.assertTrue(payload["on_trial"])
        self.assertEqual(payload["monthly_price"], "10.00")
        self.assertEqual(payload["password"], "SenhaForte123")

    @mock.patch("apps.tenants.views.SaasApiClient.create_tenant", side_effect=SaasApiTimeout("demorou"))
    def test_criacao_timeout_avisa_e_volta_para_lista(self, create_tenant):
        with mock.patch("apps.tenants.views.SaasApiClient.list_tenants", return_value=[]):
            response = self.client.post(
                reverse("tenants:create"),
                {
                    "schema_name": "novo", "client_name": "Novo", "email": "admin@novo.gov.br", "password": "SenhaForte123",
                    "primary_domain": "novo.ultradoc.test",
                },
                follow=True,
            )
        mensagens = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("pode ter continuado" in m for m in mensagens), mensagens)

    @mock.patch("apps.tenants.views.SaasApiClient.create_tenant", side_effect=SaasApiError("Já existe"))
    def test_criacao_erro_mantem_formulario(self, create_tenant):
        response = self.client.post(
            reverse("tenants:create"),
            {
                "schema_name": "novo", "client_name": "Novo", "email": "admin@novo.gov.br", "password": "SenhaForte123",
                "primary_domain": "novo.ultradoc.test",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Já existe")

    @mock.patch("apps.tenants.views.SaasApiClient.update_tenant")
    @mock.patch("apps.tenants.views.SaasApiClient.retrieve_tenant")
    def test_edicao(self, retrieve_tenant, update_tenant):
        retrieve_tenant.return_value = _tenant()
        response = self.client.get(reverse("tenants:update", args=["cliente_a"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_update"])
        self.assertEqual(response.context["form"].initial["primary_domain"], "a.ultradoc.test")

        response = self.client.post(
            reverse("tenants:update", args=["cliente_a"]),
            {
                "schema_name": "cliente_a", "client_name": "Cliente A renomeado",
                "primary_domain": "a.ultradoc.test", "paid_until": "2027-06-30", "monthly_price": "250.00",
                "manager_licenses": 3, "staff_licenses": 10, "storage_gb": 100,
            },
        )
        self.assertRedirects(response, reverse("tenants:detail", args=["cliente_a"]), fetch_redirect_response=False)
        schema, payload = update_tenant.call_args.args
        self.assertEqual(schema, "cliente_a")
        self.assertEqual(payload["client_name"], "Cliente A renomeado")
        self.assertFalse(payload["on_trial"])
        self.assertNotIn("password", payload)

    @mock.patch("apps.tenants.views.SaasApiClient.retrieve_tenant", side_effect=SaasApiError("não encontrado"))
    def test_edicao_sem_tenant_volta_para_lista(self, retrieve_tenant):
        response = self.client.get(reverse("tenants:update", args=["x"]))
        self.assertRedirects(response, reverse("tenants:list"), fetch_redirect_response=False)

    @mock.patch("apps.tenants.views.SaasApiClient.retrieve_tenant")
    def test_detalhe(self, retrieve_tenant):
        retrieve_tenant.return_value = _tenant(paid_until="2020-01-01")
        response = self.client.get(reverse("tenants:detail", args=["cliente_a"]))
        self.assertContains(response, "Vencido")
        self.assertContains(response, "Acesso bloqueado")

    @mock.patch("apps.tenants.views.SaasApiClient.retrieve_tenant")
    @mock.patch("apps.tenants.views.SaasApiClient.list_tenants")
    def test_pagamento(self, list_tenants, retrieve_tenant):
        list_tenants.return_value = [_tenant()]
        retrieve_tenant.return_value = _tenant()
        response = self.client.get(reverse("tenants:payments-create"), {"schema_name": "cliente_a"})
        self.assertEqual(response.context["form"].initial["amount"], "199.90")
        response = self.client.post(
            reverse("tenants:payments-create"),
            {"schema_name": "cliente_a", "amount": "199.90", "currency": "BRL", "status": "paid",
             "payment_date": "2026-10-01"},
        )
        self.assertRedirects(response, reverse("tenants:payments-list"), fetch_redirect_response=False)
        payment = TenantPayment.objects.get()
        self.assertEqual(payment.client_name, "Cliente A")

    def test_media_exige_login(self):
        self.client.logout()
        response = self.client.get("/media/invoices/x.pdf")
        self.assertEqual(response.status_code, 302)
