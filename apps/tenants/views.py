"""Telas de gestão dos clientes (tenants) do UltraDoc.

Nenhum dado de cliente fica neste banco: tudo vem da API ``/api/tenants/`` do
UltraDoc (``SaasApiClient``). Só os pagamentos (``TenantPayment``) são locais.
"""

import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.edit import FormView

from .forms import TenantForm, TenantPaymentForm
from .models import TenantPayment
from .services import SaasApiClient, SaasApiError, SaasApiTimeout
from .utils import STATUS_LABELS, enrich_tenant, summarize_tenants

logger = logging.getLogger(__name__)

STATUS_FILTER_CHOICES = [(key, label) for key, (label, _color) in STATUS_LABELS.items()]
ATTENTION_WINDOW_DAYS = 30


def _load_tenants(request, client=None):
    """Lista de clientes já enriquecida. Em erro, registra a mensagem e devolve
    ``([], mensagem)`` para a tela continuar utilizável."""
    client = client or SaasApiClient()
    try:
        return [enrich_tenant(t) for t in client.list_tenants()], None
    except SaasApiError as exc:
        messages.error(request, str(exc))
        return [], str(exc)


def _tenant_choices(request):
    try:
        return SaasApiClient().tenant_choices()
    except SaasApiError as exc:
        messages.error(request, str(exc))
        return []


def _plan_payload(data: dict) -> dict:
    """Campos de plano aceitos por ``create`` e ``update`` da API."""
    paid_until = data.get("paid_until")
    monthly_price = data.get("monthly_price")
    return {
        "client_name": data.get("client_name"),
        "on_trial": bool(data.get("on_trial")),
        "paid_until": paid_until.isoformat() if paid_until else None,
        "domain": data.get("primary_domain"),
        "monthly_price": str(monthly_price) if monthly_price is not None else "0",
        "manager_licenses": data.get("manager_licenses") or 0,
        "staff_licenses": data.get("staff_licenses") or 0,
        "storage_gb": data.get("storage_gb") or 0,
    }


class DashboardView(LoginRequiredMixin, View):
    template_name = "tenants/dashboard.html"

    def get(self, request):
        client = SaasApiClient()
        tenants, error = _load_tenants(request, client)
        today = date.today()
        attention = sorted(
            (
                t for t in tenants
                if t["status"] == "expired"
                or (t["days_left"] is not None and t["days_left"] <= ATTENTION_WINDOW_DAYS)
            ),
            key=lambda t: (t["paid_until"] or today),
        )
        month_start = today.replace(day=1)
        month_payments = TenantPayment.objects.filter(
            status=TenantPayment.STATUS_PAID,
            payment_date__gte=month_start,
            payment_date__lte=today,
        )
        context = {
            "api_ok": error is None and client.is_configured,
            "api_message": error or "",
            "api_base_url": client.base_url,
            "api_host_header": client.host_header,
            "summary": summarize_tenants(tenants),
            "attention": attention,
            "recent_payments": TenantPayment.objects.all()[:6],
            "payments_month_total": month_payments.aggregate(total=Sum("amount"))["total"] or 0,
            "payments_month_count": month_payments.count(),
            "today": today,
        }
        return render(request, self.template_name, context)


class TenantListView(LoginRequiredMixin, View):
    template_name = "tenants/tenant_list.html"

    def get(self, request):
        tenants, error_message = _load_tenants(request)
        query = (request.GET.get("q") or "").strip().lower()
        status = (request.GET.get("status") or "").strip()
        filtered = tenants
        if query:
            filtered = [
                t for t in filtered
                if query in (t.get("schema_name") or "").lower()
                or query in (t.get("client_name") or "").lower()
                or query in (t.get("primary_domain") or "").lower()
            ]
        if status in STATUS_LABELS:
            filtered = [t for t in filtered if t["status"] == status]
        context = {
            "tenants": filtered,
            "total_count": len(tenants),
            "error_message": error_message,
            "filter_q": request.GET.get("q") or "",
            "filter_status": status,
            "status_choices": STATUS_FILTER_CHOICES,
        }
        return render(request, self.template_name, context)


class TenantCreateView(LoginRequiredMixin, FormView):
    template_name = "tenants/tenant_form.html"
    form_class = TenantForm
    success_url = reverse_lazy("tenants:list")

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault("on_trial", True)
        initial.setdefault("manager_licenses", 0)
        initial.setdefault("staff_licenses", 0)
        initial.setdefault("storage_gb", 0)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        password = data.get("password")
        payload = _plan_payload(data)
        payload.update(
            {
                "schema_name": data.get("schema_name"),
                "email": data.get("email"),
                "password": password,
            }
        )
        client = SaasApiClient()
        try:
            created = client.create_tenant(payload)
        except SaasApiTimeout as exc:
            logger.warning("Timeout ao criar tenant %s: %s", payload["schema_name"], exc)
            messages.warning(
                self.request,
                f"{exc} A criação roda as migrations do novo schema e pode ter continuado no UltraDoc: "
                "confira se o cliente apareceu na lista antes de tentar de novo. "
                f"Senha informada para o super usuário: {password}",
            )
            return redirect(self.get_success_url())
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Cliente “{created.get('client_name') or payload['client_name']}” criado no UltraDoc "
            f"(schema {created.get('schema_name') or payload['schema_name']}, domínio {payload['domain']}). "
            f"Super usuário: {created.get('superuser_email') or payload['email']} — senha: {password}. "
            "Guarde a senha: ela não é exibida novamente.",
        )
        return redirect(reverse("tenants:detail", kwargs={"schema_name": created.get("schema_name") or payload["schema_name"]}))


class TenantUpdateView(LoginRequiredMixin, FormView):
    template_name = "tenants/tenant_form.html"
    form_class = TenantForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.schema_name = kwargs.get("schema_name")
        try:
            self.tenant = enrich_tenant(SaasApiClient().retrieve_tenant(self.schema_name))
        except SaasApiError as exc:
            messages.error(request, str(exc))
            return redirect("tenants:list")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("tenants:detail", kwargs={"schema_name": self.schema_name})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["is_update"] = True
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        tenant = self.tenant
        initial.update(
            {
                "schema_name": tenant.get("schema_name") or self.schema_name,
                "client_name": tenant.get("client_name") or "",
                "primary_domain": tenant.get("primary_domain") or "",
                "on_trial": bool(tenant.get("on_trial")),
                "paid_until": tenant.get("paid_until"),
                "manager_licenses": tenant.get("manager_licenses") or 0,
                "staff_licenses": tenant.get("staff_licenses") or 0,
                "storage_gb": tenant.get("storage_gb") or 0,
                "monthly_price": tenant.get("monthly_price"),
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        context["tenant"] = self.tenant
        return context

    def form_valid(self, form):
        payload = _plan_payload(form.cleaned_data)
        try:
            SaasApiClient().update_tenant(self.schema_name, payload)
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Cliente atualizado no UltraDoc.")
        return redirect(self.get_success_url())


class TenantDetailView(LoginRequiredMixin, View):
    template_name = "tenants/tenant_detail.html"

    def get(self, request, schema_name: str):
        tenant = None
        try:
            tenant = enrich_tenant(SaasApiClient().retrieve_tenant(schema_name))
        except SaasApiError as exc:
            messages.error(request, str(exc))
        payments = TenantPayment.objects.filter(schema_name=schema_name)
        paid_total = payments.filter(status=TenantPayment.STATUS_PAID).aggregate(total=Sum("amount"))["total"] or 0
        context = {
            "schema_name": schema_name,
            "tenant": tenant,
            "payments": payments,
            "paid_total": paid_total,
            "last_payment": payments.filter(status=TenantPayment.STATUS_PAID).first(),
        }
        return render(request, self.template_name, context)


# ----------------------------------------------------------------- pagamentos
def _apply_tenant_to_payment(request, form):
    """Preenche ``schema_name``/``client_name`` do pagamento a partir do select e da API."""
    payment = form.save(commit=False)
    schema_name = form.cleaned_data.get("schema_name")
    if schema_name:
        payment.schema_name = schema_name
        try:
            tenant = SaasApiClient().retrieve_tenant(schema_name)
            payment.client_name = tenant.get("client_name") or payment.client_name
        except SaasApiError as exc:
            # O pagamento ainda é registrado; só o nome do cliente fica como estava.
            messages.warning(request, f"Pagamento salvo, mas não foi possível consultar o cliente: {exc}")
    if not payment.currency:
        payment.currency = "BRL"
    payment.save()
    return payment


class TenantPaymentListView(LoginRequiredMixin, View):
    template_name = "tenants/payment_list.html"

    def get(self, request):
        tenant_choices = _tenant_choices(request)
        payments = TenantPayment.objects.all()
        filter_schema_name = request.GET.get("schema_name") or ""
        filter_start_date = request.GET.get("start_date") or ""
        filter_end_date = request.GET.get("end_date") or ""
        if filter_schema_name:
            payments = payments.filter(schema_name=filter_schema_name)
        if filter_start_date:
            payments = payments.filter(payment_date__gte=filter_start_date)
        if filter_end_date:
            payments = payments.filter(payment_date__lte=filter_end_date)
        context = {
            "payments": payments,
            "paid_total": payments.filter(status=TenantPayment.STATUS_PAID).aggregate(total=Sum("amount"))["total"] or 0,
            "tenant_choices": tenant_choices,
            "filter_schema_name": filter_schema_name,
            "filter_start_date": filter_start_date,
            "filter_end_date": filter_end_date,
        }
        return render(request, self.template_name, context)


class TenantPaymentCreateView(LoginRequiredMixin, FormView):
    template_name = "tenants/payment_form.html"
    form_class = TenantPaymentForm
    success_url = reverse_lazy("tenants:payments-list")

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            schema_name = request.GET.get("schema_name") or ""
            if not schema_name:
                return JsonResponse({"amount": ""})
            return JsonResponse({"amount": self.get_monthly_amount(schema_name) or ""})
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        schema_name = self.request.GET.get("schema_name")
        if schema_name:
            initial["schema_name"] = schema_name
            amount = self.get_monthly_amount(schema_name)
            if amount:
                initial["amount"] = amount
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant_choices"] = _tenant_choices(self.request)
        return kwargs

    def get_monthly_amount(self, schema_name: str):
        try:
            tenant = SaasApiClient().retrieve_tenant(schema_name)
        except SaasApiError:
            return None
        return tenant.get("monthly_price")

    def form_valid(self, form):
        _apply_tenant_to_payment(self.request, form)
        messages.success(self.request, "Pagamento registrado com sucesso.")
        return redirect(self.get_success_url())


class TenantPaymentEditView(LoginRequiredMixin, FormView):
    template_name = "tenants/payment_edit.html"
    form_class = TenantPaymentForm
    success_url = reverse_lazy("tenants:payments-list")

    def dispatch(self, request, *args, **kwargs):
        self.payment = get_object_or_404(TenantPayment, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.payment
        kwargs["tenant_choices"] = _tenant_choices(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment"] = self.payment
        return context

    def form_valid(self, form):
        _apply_tenant_to_payment(self.request, form)
        messages.success(self.request, "Pagamento atualizado com sucesso.")
        return redirect(self.get_success_url())


class TenantPaymentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        payment = get_object_or_404(TenantPayment, pk=pk)
        payment.delete()
        messages.success(request, "Pagamento excluído com sucesso.")
        return redirect("tenants:payments-list")
