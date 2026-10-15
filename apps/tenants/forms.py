import re
from datetime import date

from django import forms
from django.conf import settings

from .models import TenantPayment

# Mesmas regras do django-tenants/Postgres para nome de schema: minúsculas,
# dígitos e underscore, começando por letra, até 63 caracteres.
SCHEMA_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
RESERVED_SCHEMAS = {"public", "information_schema"}
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*$"
)


def normalize_domain(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0]
    value = value.split(":")[0]
    return value


class TenantForm(forms.Form):
    schema_name = forms.CharField(
        label="Identificador do cliente",
        max_length=63,
        help_text="Nome do schema no banco do SynDoc: letras minúsculas, números e _ (ex.: prefeitura_xyz).",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex.: prefeitura_xyz"}),
    )
    client_name = forms.CharField(
        label="Nome do Cliente",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="E-mail do super usuário",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Senha do super usuário",
        required=False,
        min_length=8,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    primary_domain = forms.CharField(
        label="Domínio principal",
        max_length=253,
        help_text="Host pelo qual o cliente acessa o SynDoc (ex.: cliente.syndoc.com.br), sem http:// nem porta.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex.: cliente.syndoc.com.br"}),
    )
    manager_licenses = forms.IntegerField(
        label="Licenças Manager",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    staff_licenses = forms.IntegerField(
        label="Licenças Staff",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    storage_gb = forms.IntegerField(
        label="Storage (GB)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    monthly_price = forms.DecimalField(
        label="Valor mensal",
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            },
        ),
    )
    on_trial = forms.BooleanField(
        label="Em período de teste",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    paid_until = forms.DateField(
        label="Pago até",
        required=False,
        help_text="Vazio = acesso sem vencimento. Data passada bloqueia o acesso do cliente no SynDoc.",
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"},
        ),
    )

    def __init__(self, *args, is_update=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_update = is_update
        if is_update:
            # Identificador e credenciais do superusuário só existem na criação.
            self.fields["schema_name"].widget.attrs["readonly"] = True
            self.fields["schema_name"].required = False
            self.fields["email"].required = False
            self.fields["password"].required = False

    def clean_schema_name(self):
        value = (self.cleaned_data.get("schema_name") or "").strip().lower()
        if self.is_update:
            return value
        if not SCHEMA_NAME_RE.match(value):
            raise forms.ValidationError(
                "Use apenas letras minúsculas, números e _ , começando por letra (máx. 63 caracteres)."
            )
        if value in RESERVED_SCHEMAS or value.startswith("pg_"):
            raise forms.ValidationError("Este identificador é reservado pelo banco de dados.")
        if value == getattr(settings, "POSTGRES_SCHEMA", ""):
            raise forms.ValidationError("Este identificador é o schema do próprio painel no banco do SynDoc.")
        return value

    def clean_primary_domain(self):
        value = normalize_domain(self.cleaned_data.get("primary_domain"))
        if not HOSTNAME_RE.match(value):
            raise forms.ValidationError(
                "Informe um host válido, sem http:// nem porta (ex.: cliente.syndoc.com.br)."
            )
        return value

    def clean(self):
        cleaned = super().clean()
        if not self.is_update and not cleaned.get("password") and not self.has_error("password"):
            self.add_error("password", "Informe uma senha ou use o botão “Gerar senha”.")
        return cleaned


class TenantPaymentForm(forms.ModelForm):
    schema_name = forms.ChoiceField(
        label="Cliente",
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            },
        ),
    )

    class Meta:
        model = TenantPayment
        fields = [
            "amount",
            "currency",
            "status",
            "payment_date",
            "reference",
            "notes",
            "invoice_file",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                },
            ),
            "currency": forms.HiddenInput(),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                },
            ),
            "payment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
            ),
            "reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                },
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                },
            ),
            "invoice_file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                },
            ),
        }

    def __init__(self, *args, tenant_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = list(tenant_choices or [])
        # Pagamento antigo de um cliente que já não existe na API continua editável.
        current = getattr(self.instance, "schema_name", None)
        if current and current not in {c[0] for c in choices}:
            choices.append((current, f"{self.instance.client_name or current} ({current})"))
        self.fields["schema_name"].choices = [("", "Selecione o cliente")] + choices
        if current:
            self.initial.setdefault("schema_name", current)
        if not self.instance.pk:
            if "payment_date" not in self.initial:
                self.initial["payment_date"] = date.today()
            if "currency" not in self.initial:
                self.initial["currency"] = "BRL"
