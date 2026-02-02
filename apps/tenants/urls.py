from django.urls import path

from .views import (
    TenantCreateView,
    TenantDetailView,
    TenantListView,
    TenantPaymentCreateView,
    TenantPaymentDeleteView,
    TenantPaymentEditView,
    TenantPaymentListView,
    TenantPaymentUpdateView,
    TenantUpdateView,
)


app_name = "tenants"


urlpatterns = [
    path("", TenantListView.as_view(), name="list"),
    path("novo/", TenantCreateView.as_view(), name="create"),
    path("pagamentos/", TenantPaymentListView.as_view(), name="payments-list"),
    path("pagamentos/novo/", TenantPaymentCreateView.as_view(), name="payments-create"),
    path("pagamentos/<int:pk>/editar/", TenantPaymentEditView.as_view(), name="payments-edit"),
    path("pagamentos/<int:pk>/excluir/", TenantPaymentDeleteView.as_view(), name="payments-delete"),
    path("<str:schema_name>/", TenantDetailView.as_view(), name="detail"),
    path("<str:schema_name>/editar/", TenantUpdateView.as_view(), name="update"),
    path("<str:schema_name>/pagamento/", TenantPaymentUpdateView.as_view(), name="payment"),
]
