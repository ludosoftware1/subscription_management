from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
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
        context = {
            "tenants": tenants,
            "error_message": error_message,
        }
        return render(request, self.template_name, context)


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
        payload = {
            "schema_name": data.get("schema_name"),
            "client_name": data.get("client_name"),
            "on_trial": data.get("on_trial"),
            "paid_until": paid_until.isoformat() if paid_until else None,
            "domain": data.get("primary_domain"),
            "manager_licenses": manager_licenses if manager_licenses is not None else 0,
            "staff_licenses": staff_licenses if staff_licenses is not None else 0,
            "storage_gb": storage_gb if storage_gb is not None else 0,
        }
        try:
            client.create_tenant(payload)
            messages.success(self.request, "Tenant criado com sucesso na API.")
            return redirect(self.get_success_url())
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)


class TenantUpdateView(LoginRequiredMixin, FormView):
    template_name = "tenants/tenant_form.html"
    form_class = TenantForm

    def get_success_url(self):
        return reverse("tenants:list")

    def get_initial(self):
        initial = super().get_initial()
        schema_name = self.kwargs.get("schema_name")
        client = SaasApiClient()
        try:
            tenant = client.retrieve_tenant(schema_name)
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return initial
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
        payload = {
            "client_name": data.get("client_name"),
            "on_trial": data.get("on_trial"),
            "paid_until": paid_until.isoformat() if paid_until else None,
            "domain": data.get("primary_domain"),
            "manager_licenses": manager_licenses if manager_licenses is not None else 0,
            "staff_licenses": staff_licenses if staff_licenses is not None else 0,
            "storage_gb": storage_gb if storage_gb is not None else 0,
        }
        try:
            client.update_tenant(schema_name, payload)
            messages.success(self.request, "Tenant atualizado com sucesso na API.")
            return redirect(self.get_success_url())
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)


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
        payment_id = request.GET.get("id")
        editing_payment = None
        if payment_id:
            editing_payment = get_object_or_404(TenantPayment, pk=payment_id)
            form = TenantPaymentForm(
                instance=editing_payment,
                tenant_choices=tenant_choices,
                initial={
                    "schema_name": editing_payment.schema_name,
                },
            )
        else:
            form = TenantPaymentForm(tenant_choices=tenant_choices)
        payments = TenantPayment.objects.all()
        context = {
            "form": form,
            "payments": payments,
            "editing_payment": editing_payment,
            "tenant_choices": tenant_choices,
        }
        return render(request, self.template_name, context)

    def post(self, request):
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
        payment_id = request.POST.get("id")
        editing_payment = None
        if payment_id:
            editing_payment = get_object_or_404(TenantPayment, pk=payment_id)
            form = TenantPaymentForm(
                request.POST,
                request.FILES,
                instance=editing_payment,
                tenant_choices=tenant_choices,
            )
        else:
            form = TenantPaymentForm(
                request.POST,
                request.FILES,
                tenant_choices=tenant_choices,
            )
        if form.is_valid():
            schema_name = form.cleaned_data.get("schema_name")
            client_name = ""
            if schema_name:
                try:
                    tenant = client.retrieve_tenant(schema_name)
                    if isinstance(tenant, dict):
                        client_name = tenant.get("client_name") or ""
                except SaasApiError as exc:
                    messages.error(request, str(exc))
            payment = form.save(commit=False)
            if schema_name:
                payment.schema_name = schema_name
            if client_name and not payment.client_name:
                payment.client_name = client_name
            if not payment.currency:
                payment.currency = "BRL"
            payment.save()
            if payment_id:
                messages.success(request, "Pagamento atualizado com sucesso.")
            else:
                messages.success(request, "Pagamento criado com sucesso.")
            return redirect("tenants:payments-list")
        payments = TenantPayment.objects.all()
        context = {
            "form": form,
            "payments": payments,
            "editing_payment": editing_payment,
            "tenant_choices": tenant_choices,
        }
        return render(request, self.template_name, context)
