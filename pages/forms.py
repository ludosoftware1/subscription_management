from django import forms
from django.contrib.auth import get_user_model
from auditlog.models import LogEntry
from django.contrib.auth import get_user_model

User = get_user_model()

class AuditLogFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Data Inicial',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        label='Data Final',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label='Usuário',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    action = forms.ChoiceField(
        choices=[('', 'Todas')] + list(LogEntry.Action.choices) + [(3, 'Login')],
        required=False,
        label='Ação',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].empty_label = "Todos os Usuários"