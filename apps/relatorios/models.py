from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class HistoricoRelatorio(models.Model):
    """Modelo para armazenar histórico de relatórios gerados"""

    TIPO_RELATORIO_CHOICES = [
        ('abastecimento_por_secretaria', 'Abastecimento por Secretaria'),
        ('gastos_por_tipo_combustivel', 'Gastos por Tipo de Combustível'),
        ('consumo_medio_por_veiculo', 'Consumo Médio por Veículo'),
        ('historico_abastecimento_por_condutor', 'Histórico de Abastecimento por Condutor'),
        ('veiculos_por_status_e_secretaria', 'Veículos por Status e Secretaria'),
        ('abastecimento_mes_veiculos_km', 'Abastecimento/Mês - Veículos, KM'),
        ('veiculos_manutencao', 'Veículos em Manutenção'),
        ('veiculos_documentacao_vencida', 'Veículos com Documentação Vencida'),
        ('condutores_documentacao_vencida', 'Condutores com Documentação Vencida'),
    ]

    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('visualizacao', 'Visualização'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    tipo_relatorio = models.CharField("Tipo de Relatório", max_length=100, choices=TIPO_RELATORIO_CHOICES)
    titulo = models.CharField("Título", max_length=200)
    formato = models.CharField("Formato", max_length=20, choices=FORMATO_CHOICES, default='visualizacao')

    # Filtros aplicados (removed ForeignKeys to removed models)
    data_inicial = models.DateField("Data Inicial", null=True, blank=True)
    data_final = models.DateField("Data Final", null=True, blank=True)

    # Metadados
    data_geracao = models.DateTimeField("Data de Geração", default=timezone.now)
    numero_registros = models.PositiveIntegerField("Número de Registros", default=0)
    filtros_aplicados = models.JSONField("Filtros Aplicados", default=dict, blank=True)

    # Controle de sessão (para abas múltiplas)
    sessao_id = models.CharField("ID da Sessão", max_length=100, blank=True)
    aba_id = models.CharField("ID da Aba", max_length=50, blank=True)

    class Meta:
        app_label = 'apps.relatorios'
        verbose_name = "Histórico de Relatório"
        verbose_name_plural = "Histórico de Relatórios"
        ordering = ['-data_geracao']

    def __str__(self):
        return f"{self.titulo} - {self.usuario.get_full_name() or self.usuario.username} ({self.data_geracao.strftime('%d/%m/%Y %H:%M')})"

    def get_tipo_display(self):
        return dict(self.TIPO_RELATORIO_CHOICES).get(self.tipo_relatorio, self.tipo_relatorio)

    def get_formato_display(self):
        return dict(self.FORMATO_CHOICES).get(self.formato, self.formato)
