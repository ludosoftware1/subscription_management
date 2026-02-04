from datetime import date
import secrets
import string

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.edit import FormView

from .forms import TenantForm, TenantPaymentForm
from .models import TenantPayment
from .services import SaasApiClient, SaasApiError


class TenantListView(LoginRequiredMixin, View):
    template_name = "tenants/tenant_list.html"

    def get(self, request):
        client = SaasApiClient()
        tenants = []
        error_message = None
        try:
            tenants = client.list_tenants()
        except SaasApiError as exc:
            error_message = str(exc)
            messages.error(request, error_message)
        for tenant in tenants:
            for key in ("paid_until", "created_on"):
                value = tenant.get(key)
                if isinstance(value, str):
                    try:
                        tenant[key] = date.fromisoformat(value)
                    except ValueError:
                        continue
        context = {
            "tenants": tenants,
            "error_message": error_message,
        }
        return render(request, self.template_name, context)


class TenantPaymentEditView(LoginRequiredMixin, FormView):
    template_name = "tenants/payment_edit.html"
    form_class = TenantPaymentForm

    def dispatch(self, request, *args, **kwargs):
        self.payment = get_object_or_404(TenantPayment, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("tenants:payments-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        client = SaasApiClient()
        tenant_choices = []
        try:
            tenants = client.list_tenants()
            tenant_choices = [
                (t.get("schema_name"), f'{t.get("client_name")} ({t.get("schema_name")})')
                for t in tenants
                if t.get("schema_name")
            ]
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
        kwargs["instance"] = self.payment
        kwargs["tenant_choices"] = tenant_choices
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment"] = self.payment
        return context

    def form_valid(self, form):
        client = SaasApiClient()
        schema_name = form.cleaned_data.get("schema_name")
        client_name = ""
        if schema_name:
            try:
                tenant = client.retrieve_tenant(schema_name)
                if isinstance(tenant, dict):
                    client_name = tenant.get("client_name") or ""
            except SaasApiError as exc:
                messages.error(self.request, str(exc))
        payment = form.save(commit=False)
        if schema_name:
            payment.schema_name = schema_name
        if client_name and not payment.client_name:
            payment.client_name = client_name
        if not payment.currency:
            payment.currency = "BRL"
        payment.save()
        messages.success(self.request, "Pagamento atualizado com sucesso.")
        return redirect(self.get_success_url())


class TenantPaymentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        payment = get_object_or_404(TenantPayment, pk=pk)
        payment.delete()
        messages.success(request, "Pagamento excluído com sucesso.")
        return redirect("tenants:payments-list")


class TenantCreateView(LoginRequiredMixin, FormView):
    template_name = "tenants/tenant_form.html"
    form_class = TenantForm
    success_url = reverse_lazy("tenants:list")

    def form_valid(self, form):
        client = SaasApiClient()
        data = form.cleaned_data
        paid_until = data.get("paid_until")
        manager_licenses = data.get("manager_licenses")
        staff_licenses = data.get("staff_licenses")
        storage_gb = data.get("storage_gb")
        monthly_price = data.get("monthly_price")
        email = data.get("email")
        password = data.get("password") or ""
        generate_password = data.get("generate_password")

        if generate_password and not password:
            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for _ in range(12))
            form.data = form.data.copy()
            form.data["password"] = password
        elif not password:
            form.add_error(
                "password",
                "Informe uma senha ou marque a opção de gerar automaticamente.",
            )
            return self.form_invalid(form)

        payload = {
            "schema_name": data.get("schema_name"),
            "client_name": data.get("client_name"),
            "on_trial": data.get("on_trial"),
            "paid_until": paid_until.isoformat() if paid_until else None,
            "domain": data.get("primary_domain"),
            "email": email,
            "password": password,
            "monthly_price": float(monthly_price) if monthly_price is not None else 0,
            "manager_licenses": manager_licenses if manager_licenses is not None else 0,
            "staff_licenses": staff_licenses if staff_licenses is not None else 0,
            "storage_gb": storage_gb if storage_gb is not None else 0,
        }
        try:
            client.create_tenant(payload)
            messages.success(
                self.request,
                f"Tenant criado com sucesso na API. Senha do super usuário: {password}",
            )
            return redirect(self.get_success_url())
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)


class TenantUpdateView(LoginRequiredMixin, FormView):
    template_name = "tenants/tenant_form.html"
    form_class = TenantForm

    def get_success_url(self):
        return reverse("tenants:list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        field = form.fields.get("schema_name")
        if field is not None:
            attrs = field.widget.attrs
            attrs["readonly"] = True
        email_field = form.fields.get("email")
        if email_field is not None:
            email_field.required = False
        return form

    def get_initial(self):
        initial = super().get_initial()
        schema_name = self.kwargs.get("schema_name")
        client = SaasApiClient()
        try:
            tenant = client.retrieve_tenant(schema_name)
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return initial
        monthly_price = None
        if isinstance(tenant, dict):
            for key in ("monthly_price", "monthly_amount", "monthly_value", "valor_mensal", "monthly_fee"):
                value = tenant.get(key)
                if value is not None:
                    monthly_price = value
                    break
        initial.update(
            {
                "schema_name": tenant.get("schema_name") or "",
                "client_name": tenant.get("client_name") or "",
                "primary_domain": tenant.get("primary_domain") or "",
                "on_trial": tenant.get("on_trial") if tenant.get("on_trial") is not None else False,
                "paid_until": tenant.get("paid_until") or None,
                "manager_licenses": tenant.get("manager_licenses") if tenant.get("manager_licenses") is not None else 0,
                "staff_licenses": tenant.get("staff_licenses") if tenant.get("staff_licenses") is not None else 0,
                "storage_gb": tenant.get("storage_gb") if tenant.get("storage_gb") is not None else 0,
                "monthly_price": monthly_price,
            }
        )
        return initial

    def form_valid(self, form):
        client = SaasApiClient()
        schema_name = self.kwargs.get("schema_name")
        data = form.cleaned_data
        paid_until = data.get("paid_until")
        manager_licenses = data.get("manager_licenses")
        staff_licenses = data.get("staff_licenses")
        storage_gb = data.get("storage_gb")
        monthly_price = data.get("monthly_price")
        payload = {
            "client_name": data.get("client_name"),
            "on_trial": data.get("on_trial"),
            "paid_until": paid_until.isoformat() if paid_until else None,
            "domain": data.get("primary_domain"),
            "manager_licenses": manager_licenses if manager_licenses is not None else 0,
            "staff_licenses": staff_licenses if staff_licenses is not None else 0,
            "storage_gb": storage_gb if storage_gb is not None else 0,
        }
        if monthly_price is not None:
            payload["monthly_price"] = float(monthly_price)
        try:
            client.update_tenant(schema_name, payload)
            messages.success(self.request, "Tenant atualizado com sucesso na API.")
            return redirect(self.get_success_url())
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)


class TenantDetailView(LoginRequiredMixin, View):
    template_name = "tenants/tenant_detail.html"

    def get(self, request, schema_name: str):
        client = SaasApiClient()
        tenant = None
        try:
            tenant = client.retrieve_tenant(schema_name)
        except SaasApiError as exc:
            messages.error(request, str(exc))
        if isinstance(tenant, dict):
            for key in ("paid_until", "created_on"):
                value = tenant.get(key)
                if isinstance(value, str):
                    try:
                        tenant[key] = date.fromisoformat(value)
                    except ValueError:
                        continue
        payments = TenantPayment.objects.filter(schema_name=schema_name)
        context = {
            "schema_name": schema_name,
            "tenant": tenant,
            "payments": payments,
        }
        return render(request, self.template_name, context)

class TenantPaymentUpdateView(LoginRequiredMixin, FormView):
    template_name = "tenants/tenant_payment_form.html"
    form_class = TenantPaymentForm

    def get_success_url(self):
        return reverse("tenants:payment", kwargs={"schema_name": self.kwargs.get("schema_name")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schema_name = self.kwargs.get("schema_name")
        client = SaasApiClient()
        tenant = None
        try:
            tenant = client.retrieve_tenant(schema_name)
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
        context.update(
            {
                "schema_name": schema_name,
                "tenant": tenant,
                "payments": TenantPayment.objects.filter(schema_name=schema_name),
            }
        )
        return context

    def form_valid(self, form):
        schema_name = self.kwargs.get("schema_name")
        client = SaasApiClient()
        try:
            tenant = client.retrieve_tenant(schema_name)
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            tenant = None
        client_name = ""
        if isinstance(tenant, dict):
            client_name = tenant.get("client_name") or ""
        payment = form.save(commit=False)
        payment.schema_name = schema_name
        if not payment.client_name:
            payment.client_name = client_name
        payment.save()
        messages.success(self.request, "Pagamento registrado com sucesso.")
        return redirect(self.get_success_url())


class TenantPaymentListView(LoginRequiredMixin, View):
    template_name = "tenants/payment_list.html"

    def get(self, request):
        client = SaasApiClient()
        tenant_choices = []
        try:
            tenants = client.list_tenants()
            tenant_choices = [
                (t.get("schema_name"), f'{t.get("client_name")} ({t.get("schema_name")})')
                for t in tenants
                if t.get("schema_name")
            ]
        except SaasApiError as exc:
            messages.error(request, str(exc))
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
            "tenant_choices": tenant_choices,
            "filter_schema_name": filter_schema_name,
            "filter_start_date": filter_start_date,
            "filter_end_date": filter_end_date,
        }
        return render(request, self.template_name, context)

class TenantPaymentCreateView(LoginRequiredMixin, FormView):
    template_name = "tenants/payment_form.html"
    form_class = TenantPaymentForm

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            schema_name = request.GET.get("schema_name") or ""
            if not schema_name:
                return JsonResponse({"amount": ""})
            amount = self.get_monthly_amount(schema_name)
            return JsonResponse({"amount": amount or ""})
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("tenants:payments-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        client = SaasApiClient()
        tenant_choices = []
        try:
            tenants = client.list_tenants()
            tenant_choices = [
                (t.get("schema_name"), f'{t.get("client_name")} ({t.get("schema_name")})')
                for t in tenants
                if t.get("schema_name")
            ]
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
        kwargs["tenant_choices"] = tenant_choices
        return kwargs

    def get_monthly_amount(self, schema_name: str):
        client = SaasApiClient()
        try:
            tenant = client.retrieve_tenant(schema_name)
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return None
        if not isinstance(tenant, dict):
            return None
        for key in ("monthly_price", "monthly_amount", "monthly_value", "valor_mensal", "monthly_fee"):
            value = tenant.get(key)
            if value is not None:
                return value
        return None

    def form_valid(self, form):
        client = SaasApiClient()
        schema_name = form.cleaned_data.get("schema_name")
        client_name = ""
        if schema_name:
            try:
                tenant = client.retrieve_tenant(schema_name)
                if isinstance(tenant, dict):
                    client_name = tenant.get("client_name") or ""
            except SaasApiError as exc:
                messages.error(self.request, str(exc))
        payment = form.save(commit=False)
        if schema_name:
            payment.schema_name = schema_name
        if client_name and not payment.client_name:
            payment.client_name = client_name
        if not payment.currency:
            payment.currency = "BRL"
        payment.save()
        messages.success(self.request, "Pagamento criado com sucesso.")
        return redirect(self.get_success_url())
