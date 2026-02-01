from django import forms
from .models_configuracao import ConfiguracaoSite, ConfiguracaoEmail

class ConfiguracaoSiteForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSite
        fields = ['logo_principal', 'favicon', 'logo_login', 'subtitulo_login', 'footer_text1', 'footer_text2']
        widgets = {
            'logo_principal': forms.ClearableFileInput(attrs={'style': 'display: none;'}),
            'favicon': forms.ClearableFileInput(attrs={'style': 'display: none;'}),
            'logo_login': forms.ClearableFileInput(attrs={'style': 'display: none;'}),
            'subtitulo_login': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_text1': forms.TextInput(attrs={'class': 'form-control'}),
            'footer_text2': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ConfiguracaoEmailForm(forms.ModelForm):
    smtp_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a senha SMTP'
        }),
        required=True,
        help_text='Senha para autenticação no servidor SMTP'
    )
    
    class Meta:
        model = ConfiguracaoEmail
        fields = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'use_tls', 'use_ssl']
        widgets = {
            'smtp_host': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'smtp.exemplo.com'
            }),
            'smtp_port': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '587'
            }),
            'smtp_user': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'seu-email@exemplo.com'
            }),
            'use_tls': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'use_ssl': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'smtp_host': 'Servidor SMTP',
            'smtp_port': 'Porta SMTP',
            'smtp_user': 'Usuário SMTP',
            'smtp_password': 'Senha SMTP',
            'use_tls': 'Usar TLS',
            'use_ssl': 'Usar SSL',
        }
