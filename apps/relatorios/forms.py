from django import forms

class RelatorioForm(forms.Form):
    REPORT_CHOICES = [
        ('abastecimento_por_secretaria', 'Abastecimento por Secretaria'),
        ('gastos_por_tipo_combustivel', 'Gastos por Tipo de Combustível'),
        ('consumo_medio_por_veiculo', 'Consumo Médio por Veículo'),
        ('historico_abastecimento_por_condutor', 'Histórico de Abastecimento por Condutor'),
        ('veiculos_por_status_e_secretaria', 'Veículos por Status e Secretaria'),
        ('abastecimento_mes_veiculos_km', 'Abastecimento/Mês - Veículos, KM Inicial/Final'),
        ('veiculos_manutencao', 'Veículos em Manutenção'),
        ('veiculos_documentacao_vencida', 'Veículos com Documentação Vencida'),
        ('condutores_documentacao_vencida', 'Condutores com Documentação Vencida'),
    ]

    report_type = forms.ChoiceField(choices=REPORT_CHOICES, label="Tipo de Relatório")
    data_inicial = forms.DateField(label="Data Inicial", required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    data_final = forms.DateField(label="Data Final", required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    # Removed fields dependent on removed models
