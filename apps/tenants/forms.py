from datetime import date

from django import forms

from .models import TenantPayment


class TenantForm(forms.Form):
    schema_name = forms.CharField(
        label="Schema",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    client_name = forms.CharField(
        label="Nome do Cliente",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    primary_domain = forms.CharField(
        label="Domínio principal",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
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
    on_trial = forms.BooleanField(
        label="Em período de teste",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    paid_until = forms.DateField(
        label="Pago até",
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"},
        ),
    )


class TenantPaymentForm(forms.ModelForm):
    schema_name = forms.ChoiceField(
        label="Cliente",
        required=False,
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
        choices = tenant_choices or []
        self.fields["schema_name"].choices = choices
        if not self.instance.pk:
            if "payment_date" not in self.initial:
                self.initial["payment_date"] = date.today()
            if "currency" not in self.initial:
                self.initial["currency"] = "BRL"
