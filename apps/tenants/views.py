from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.edit import FormView

from .forms import TenantForm
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
        payload = {
            "schema_name": data.get("schema_name"),
            "client_name": data.get("client_name"),
            "on_trial": data.get("on_trial"),
            "paid_until": paid_until.isoformat() if paid_until else None,
            "domain": data.get("primary_domain"),
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
            }
        )
        return initial

    def form_valid(self, form):
        client = SaasApiClient()
        schema_name = self.kwargs.get("schema_name")
        data = form.cleaned_data
        paid_until = data.get("paid_until")
        payload = {
            "client_name": data.get("client_name"),
            "on_trial": data.get("on_trial"),
            "paid_until": paid_until.isoformat() if paid_until else None,
            "domain": data.get("primary_domain"),
        }
        try:
            client.update_tenant(schema_name, payload)
            messages.success(self.request, "Tenant atualizado com sucesso na API.")
            return redirect(self.get_success_url())
        except SaasApiError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
