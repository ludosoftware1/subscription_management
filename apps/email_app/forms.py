from django import forms

class EmailTestForm(forms.Form):
    TEMPLATE_CHOICES = [
        ('aprovacao_solicitacao.html', 'Aprovação de Solicitação'),
        ('reprovacao_solicitacao.html', 'Reprovação de Solicitação'),
        ('aprovacao_inscricao.html', 'Aprovação de Inscrição'),
        ('reprovacao_inscricao.html', 'Reprovação de Inscrição'),
        ('boas_vindas.html', 'Boas-Vindas'),
        ('notificacao_pendencias.html', 'Notificação de Pendências'),
        ('confirmacao_inscricao.html', 'Confirmação de Inscrição'),
        # Adicione outros templates conforme necessário
    ]

    to_email = forms.EmailField(label="E-mail do Destinatário", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    template_name = forms.ChoiceField(label="Tipo de E-mail", choices=TEMPLATE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    observacao = forms.CharField(label="Observação/Justificativa (para reprovação/pendências)", widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)
