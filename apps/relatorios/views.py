from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RelatorioForm
from .models import HistoricoRelatorio
from apps.configuracao.models_configuracao import ConfiguracaoSite
from django.db import models
from django.db.models import Sum, F
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import json

class RelatorioSelectionView(View):

    # Mapeamento de códigos para nomes de combustível
    TIPO_COMBUSTIVEL_MAP = {
        1: 'Gasolina',
        2: 'Diesel',
        3: 'Etanol',
        4: 'Gás Natural (GNV)',
        5: 'Flex (Gasolina/Etanol)',
        6: 'Elétrico',
        'gasolina': 'Gasolina',
        'diesel': 'Diesel',
        'etanol': 'Etanol',
        'gas_natural': 'Gás Natural',
    }

    def get_tipo_combustivel_display(self, tipo_combustivel):
        """Converte código ou string de combustível para nome legível"""
        if tipo_combustivel is None:
            return 'N/A'
        return self.TIPO_COMBUSTIVEL_MAP.get(tipo_combustivel, str(tipo_combustivel))

    def formatar_moeda_br(self, valor):
        """Formata valor monetário no padrão brasileiro (R$ 1.234,56)"""
        if valor is None or valor == 0:
            return 'R$ 0,00'

        try:
            # Converte para float se necessário
            valor_float = float(valor)

            # Formata com separadores brasileiros
            # Primeiro formata com ponto para milhares e vírgula para decimais
            valor_formatado = f"{valor_float:,.2f}"

            # Substitui ponto por espaço temporário, vírgula por ponto, e espaço por vírgula
            valor_formatado = valor_formatado.replace('.', ' ').replace(',', '.').replace(' ', ',')

            return f"R$ {valor_formatado}"
        except (ValueError, TypeError):
            return f"R$ {valor}"

    def get(self, request, *args, **kwargs):
        form = RelatorioForm()
        return render(request, 'relatorios/report_selection.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = RelatorioForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            data_inicial = form.cleaned_data['data_inicial']
            data_final = form.cleaned_data['data_final']
            veiculo = form.cleaned_data['veiculo']
            condutor = form.cleaned_data['condutor']
            secretaria = form.cleaned_data['secretaria']

            context = {
                'form': form,
                'report_type': report_type,
                'data_inicial': data_inicial,
                'data_final': data_final,
                'veiculo': veiculo,
                'condutor': condutor,
                'secretaria': secretaria,
                'report_data': None,
                'report_title': '',
            }

            if report_type == 'abastecimento_por_secretaria':
                context.update(self._generate_abastecimento_por_secretaria(data_inicial, data_final, secretaria))
            elif report_type == 'gastos_por_tipo_combustivel':
                context.update(self._generate_gastos_por_tipo_combustivel(data_inicial, data_final))
            elif report_type == 'consumo_medio_por_veiculo':
                context.update(self._generate_consumo_medio_por_veiculo(data_inicial, data_final, veiculo))
            elif report_type == 'historico_abastecimento_por_condutor':
                context.update(self._generate_historico_abastecimento_por_condutor(data_inicial, data_final, condutor))
            elif report_type == 'veiculos_por_status_e_secretaria':
                context.update(self._generate_veiculos_por_status_e_secretaria(secretaria))
            elif report_type == 'abastecimento_mes_veiculos_km':
                context.update(self._generate_abastecimento_mes_veiculos_km(data_inicial, data_final, None))
            elif report_type == 'veiculos_manutencao':
                context.update(self._generate_veiculos_manutencao())
            elif report_type == 'veiculos_documentacao_vencida':
                context.update(self._generate_veiculos_documentacao_vencida())
            elif report_type == 'condutores_documentacao_vencida':
                context.update(self._generate_condutores_documentacao_vencida())

            return render(request, 'relatorios/report_selection.html', context)
        return render(request, 'relatorios/report_selection.html', {'form': form})

    def _generate_abastecimento_por_secretaria(self, data_inicial, data_final, secretaria_filter):
        # Models removed, return empty data
        return {
            'report_title': 'Abastecimento por Secretaria',
            'report_data': [],
            'report_template': 'relatorios/partials/abastecimento_por_secretaria_table.html'
        }

    def _generate_gastos_por_tipo_combustivel(self, data_inicial, data_final):
        # Models removed, return empty data
        return {
            'report_title': 'Gastos por Tipo de Combustível',
            'report_data': [],
            'report_template': 'relatorios/partials/gastos_por_tipo_combustivel_table.html'
        }

    def _generate_consumo_medio_por_veiculo(self, data_inicial, data_final, veiculo_filter):
        # Models removed, return empty data
        return {
            'report_title': 'Consumo Médio por Veículo',
            'report_data': [],
            'report_template': 'relatorios/partials/consumo_medio_por_veiculo_table.html'
        }

    def _generate_historico_abastecimento_por_condutor(self, data_inicial, data_final, condutor_filter):
        # Models removed, return empty data
        return {
            'report_title': 'Histórico de Abastecimento por Condutor',
            'report_data': [],
            'report_template': 'relatorios/partials/historico_abastecimento_por_condutor_table.html'
        }

    def _generate_veiculos_por_status_e_secretaria(self, secretaria_filter):
        # Models removed, return empty data
        return {
            'report_title': 'Veículos por Status e Secretaria',
            'report_data': [],
            'report_template': 'relatorios/partials/veiculos_por_status_e_secretaria_table.html'
        }

    def _generate_abastecimento_mes_veiculos_km(self, data_inicial, data_final, veiculo_filter):
        # Models removed, return empty data
        return {
            'report_title': 'Abastecimento/Mês - Veículos, KM Inicial/Final',
            'report_data': [],
            'report_template': 'relatorios/partials/abastecimento_mes_veiculos_km_table.html'
        }

    def _generate_veiculos_manutencao(self):
        # Models removed, return empty data
        return {
            'report_title': 'Veículos em Manutenção',
            'report_data': [],
            'report_template': 'relatorios/partials/veiculos_manutencao_table.html'
        }

    def _generate_veiculos_documentacao_vencida(self):
        # Models removed, return empty data
        return {
            'report_title': 'Veículos com Documentação Vencida',
            'report_data': [],
            'report_template': 'relatorios/partials/veiculos_documentacao_vencida_table.html'
        }

    def _generate_condutores_documentacao_vencida(self):
        # Models removed, return empty data
        return {
            'report_title': 'Condutores com Documentação Vencida',
            'report_data': [],
            'report_template': 'relatorios/partials/condutores_documentacao_vencida_table.html'
        }


class CentroRelatoriosView(LoginRequiredMixin, RelatorioSelectionView):
    """Centro de Relatórios Corporativo - Interface profissional para geração de relatórios"""

    def get(self, request, *args, **kwargs):
        # Models removed, use empty querysets
        context = {
            'veiculos': [],
            'condutores': [],
            'secretarias': [],
        }

        return render(request, 'relatorios/centro_relatorios.html', context)

    def post(self, request, *args, **kwargs):
        """API para gerar relatórios via AJAX"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

        action = request.POST.get('action')

        if action == 'generate_report':
            return self._generate_report_ajax(request)
        elif action == 'get_history':
            return self._get_history_ajax(request)
        elif action == 'save_to_history':
            return self._save_to_history_ajax(request)

        return JsonResponse({'error': 'Ação não reconhecida'}, status=400)

    def _generate_report_ajax(self, request):
        """Gera relatório via AJAX para pré-visualização"""
        report_type = request.POST.get('report_type')
        data_inicial = request.POST.get('data_inicial') or None
        data_final = request.POST.get('data_final') or None
        veiculo_id = request.POST.get('veiculo')
        condutor_id = request.POST.get('condutor')
        secretaria_id = request.POST.get('secretaria')

        # Models removed, set to None
        veiculo = None
        condutor = None
        secretaria = None

        # Gerar relatório usando os métodos existentes
        result = {}
        if report_type == 'abastecimento_por_secretaria':
            result = self._generate_abastecimento_por_secretaria(data_inicial, data_final, secretaria)
        elif report_type == 'gastos_por_tipo_combustivel':
            result = self._generate_gastos_por_tipo_combustivel(data_inicial, data_final)
        elif report_type == 'consumo_medio_por_veiculo':
            result = self._generate_consumo_medio_por_veiculo(data_inicial, data_final, veiculo)
        elif report_type == 'historico_abastecimento_por_condutor':
            result = self._generate_historico_abastecimento_por_condutor(data_inicial, data_final, condutor)
        elif report_type == 'veiculos_por_status_e_secretaria':
            result = self._generate_veiculos_por_status_e_secretaria(secretaria)
        elif report_type == 'abastecimento_mes_veiculos_km':
            result = self._generate_abastecimento_mes_veiculos_km(data_inicial, data_final, veiculo)
        elif report_type == 'veiculos_manutencao':
            result = self._generate_veiculos_manutencao()
        elif report_type == 'veiculos_documentacao_vencida':
            result = self._generate_veiculos_documentacao_vencida()
        elif report_type == 'condutores_documentacao_vencida':
            result = self._generate_condutores_documentacao_vencida()

        # Salvar no histórico automaticamente
        filtros_aplicados = {
            'data_inicial': data_inicial,
            'data_final': data_final,
            'veiculo_id': veiculo_id,
            'condutor_id': condutor_id,
            'secretaria_id': secretaria_id,
        }

        HistoricoRelatorio.objects.create(
            usuario=request.user,
            tipo_relatorio=report_type,
            titulo=result.get('report_title', 'Relatório'),
            formato='visualizacao',
            data_inicial=data_inicial,
            data_final=data_final,
            numero_registros=len(result.get('report_data', [])),
            filtros_aplicados=filtros_aplicados,
        )

        return JsonResponse({
            'success': True,
            'report_title': result.get('report_title'),
            'report_data': result.get('report_data'),
            'record_count': len(result.get('report_data', []))
        })

    def _get_history_ajax(self, request):
        """Obtém histórico de relatórios do usuário"""
        limit = int(request.POST.get('limit', 10))
        history = HistoricoRelatorio.objects.filter(
            usuario=request.user
        ).order_by('-data_geracao')[:limit]

        history_data = []
        for item in history:
            history_data.append({
                'id': item.id,
                'titulo': item.titulo,
                'tipo_relatorio': item.get_tipo_display(),
                'formato': item.get_formato_display(),
                'data_geracao': item.data_geracao.strftime('%d/%m/%Y %H:%M'),
                'numero_registros': item.numero_registros,
                'filtros_aplicados': item.filtros_aplicados,
            })

        return JsonResponse({
            'success': True,
            'history': history_data
        })

    def _save_to_history_ajax(self, request):
        """Salva relatório específico no histórico"""
        report_type = request.POST.get('report_type')
        titulo = request.POST.get('titulo', 'Relatório Salvo')

        # Criar entrada no histórico
        HistoricoRelatorio.objects.create(
            usuario=request.user,
            tipo_relatorio=report_type,
            titulo=titulo,
            formato='visualizacao',
        )

        return JsonResponse({
            'success': True,
            'message': 'Relatório salvo no histórico'
        })

def export_report_to_excel(request):
    report_type = request.GET.get('report_type')
    data_inicial = request.GET.get('data_inicial')
    data_final = request.GET.get('data_final')
    veiculo_id = request.GET.get('veiculo')
    condutor_id = request.GET.get('condutor')
    secretaria_id = request.GET.get('secretaria')

    # Re-run the report generation logic to get the data
    view = RelatorioSelectionView()
    form_data = {
        'report_type': report_type,
        'data_inicial': data_inicial,
        'data_final': data_final,
        'veiculo': veiculo_id,
        'condutor': condutor_id,
        'secretaria': secretaria_id,
    }
    form = RelatorioForm(form_data)
    
    report_data = []
    report_title = "Relatório"

    if form.is_valid():
        # Convert IDs back to model instances for the generation functions
        veiculo = Veiculo.objects.get(id=veiculo_id) if veiculo_id else None
        condutor = Condutor.objects.get(id=condutor_id) if condutor_id else None
        secretaria = Secretaria.objects.get(id=secretaria_id) if secretaria_id else None

        if report_type == 'abastecimento_por_secretaria':
            result = view._generate_abastecimento_por_secretaria(data_inicial, data_final, secretaria)
            report_data = result['report_data']
            report_title = result['report_title']
            df = pd.DataFrame(list(report_data))
            df.rename(columns={
                'veiculo__secretaria__nome': 'Secretaria',
                'tipo_combustivel': 'Tipo de Combustível',
                'total_litros': 'Total Litros',
                'total_valor': 'Total Valor (R$)'
            }, inplace=True)
        elif report_type == 'gastos_por_tipo_combustivel':
            result = view._generate_gastos_por_tipo_combustivel(data_inicial, data_final)
            report_data = result['report_data']
            report_title = result['report_title']
            df = pd.DataFrame(list(report_data))
            df.rename(columns={
                'tipo_combustivel': 'Tipo de Combustível',
                'total_litros': 'Total Litros',
                'total_valor': 'Total Valor (R$)'
            }, inplace=True)
        elif report_type == 'consumo_medio_por_veiculo':
            result = view._generate_consumo_medio_por_veiculo(data_inicial, data_final, veiculo)
            report_data = result['report_data']
            report_title = result['report_title']
            df = pd.DataFrame(list(report_data))
            df.rename(columns={
                'veiculo__placa': 'Placa do Veículo',
                'veiculo__modelo': 'Modelo do Veículo',
                'total_litros': 'Total Litros',
                'distancia_total': 'Distância Total (KM)',
                'media_consumo': 'Média de Consumo (KM/L)'
            }, inplace=True)
        elif report_type == 'historico_abastecimento_por_condutor':
            result = view._generate_historico_abastecimento_por_condutor(data_inicial, data_final, condutor)
            report_data = result['report_data']
            report_title = result['report_title']
            data = []
            for item in report_data:
                data.append({
                    'Condutor': item['condutor_nome'],
                    'Data': item['data_abastecimento'],
                    'KM Atual': item['quilometragem_atual'],
                    'Tipo Combustível': item['tipo_combustivel'],
                    'Litros': item['litros'],
                    'Valor Litro': f"R$ {item['valor_litro']:.2f}" if item['valor_litro'] else 'N/A',
                    'Valor Total': f"R$ {item['valor_total']:.2f}",
                })
            df = pd.DataFrame(data) if data else pd.DataFrame([{'Mensagem': 'Dados não disponíveis para export'}])
        elif report_type == 'veiculos_por_status_e_secretaria':
            result = view._generate_veiculos_por_status_e_secretaria(secretaria)
            report_data = result['report_data']
            report_title = result['report_title']
            df = pd.DataFrame(list(report_data))
            df.rename(columns={
                'secretaria__nome': 'Secretaria',
                'situacao': 'Status do Veículo',
                'count': 'Quantidade'
            }, inplace=True)
    else:
        return HttpResponse("Erro nos parâmetros do relatório.", status=400)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=report_title)
    output.seek(0)

    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{report_title}.xlsx"'
    return response

def add_header_and_footer(canvas, doc, configuracao=None):
    """Adiciona cabeçalho e rodapé em todas as páginas"""
    page_num = canvas.getPageNumber()

    # CABEÇALHO - sempre no topo de cada página
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.darkblue)

    # Logo no cabeçalho (esquerda)
    if configuracao and configuracao.logo_principal:
        try:
            logo_path = configuracao.logo_principal.path
            canvas.drawImage(logo_path, 0.5*inch, 10.5*inch, width=1*inch, height=0.5*inch, mask='auto')
        except:
            pass

    # Nome da prefeitura no cabeçalho (centro)
    nome_prefeitura = configuracao.nome_prefeitura if configuracao and configuracao.nome_prefeitura else "PREFEITURA MUNICIPAL"
    canvas.drawCentredString(4.25*inch, 10.7*inch, nome_prefeitura)

    # Sistema no cabeçalho (direita)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.gray)
    canvas.drawRightString(7.5*inch, 10.7*inch, "Sistema de Gestão de Frotas")

    # Linha separadora do cabeçalho
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(0.5*inch, 10.3*inch, 7.5*inch, 10.3*inch)

    # RODAPÉ
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.gray)

    # Informações da prefeitura no rodapé esquerdo
    footer_left = ""
    if configuracao:
        if configuracao.footer_text1:
            footer_left += configuracao.footer_text1
        if configuracao.footer_text2:
            if footer_left:
                footer_left += " | "
            footer_left += configuracao.footer_text2

    # Desenhar informações da prefeitura à esquerda
    if footer_left:
        canvas.drawString(0.5*inch, 0.5*inch, footer_left)

    # Numeração de página à direita
    page_text = f"Página {page_num}"
    canvas.drawRightString(7.5*inch, 0.5*inch, page_text)

    # Linha separadora do rodapé
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(0.5*inch, 0.8*inch, 7.5*inch, 0.8*inch)

def export_report_to_pdf(request):
    report_type = request.GET.get('report_type')
    data_inicial = request.GET.get('data_inicial')
    data_final = request.GET.get('data_final')
    veiculo_id = request.GET.get('veiculo')
    condutor_id = request.GET.get('condutor')
    secretaria_id = request.GET.get('secretaria')

    view = RelatorioSelectionView()
    form_data = {
        'report_type': report_type,
        'data_inicial': data_inicial,
        'data_final': data_final,
        'veiculo': veiculo_id,
        'condutor': condutor_id,
        'secretaria': secretaria_id,
    }
    form = RelatorioForm(form_data)

    report_data = []
    report_title = "Relatório"
    headers = []
    data_for_pdf = []

    if form.is_valid():
        veiculo = Veiculo.objects.get(id=veiculo_id) if veiculo_id else None
        condutor = Condutor.objects.get(id=condutor_id) if condutor_id else None
        secretaria = Secretaria.objects.get(id=secretaria_id) if secretaria_id else None

        if report_type == 'abastecimento_por_secretaria':
            result = view._generate_abastecimento_por_secretaria(data_inicial, data_final, secretaria)
            report_data = result['report_data']
            report_title = result['report_title']
            headers = ['Secretaria', 'Tipo de Combustível', 'Total Litros', 'Total Valor (R$)']
            for item in report_data:
                data_for_pdf.append([
                    item['secretaria_nome'],
                    item['tipo_combustivel'],
                    f"{item['total_litros']:.2f}",
                    f"R$ {item['total_valor']:.2f}"
                ])
        elif report_type == 'gastos_por_tipo_combustivel':
            result = view._generate_gastos_por_tipo_combustivel(data_inicial, data_final)
            report_data = result['report_data']
            report_title = result['report_title']
            headers = ['Tipo de Combustível', 'Total Litros', 'Total Valor (R$)']
            for item in report_data:
                data_for_pdf.append([
                    item['tipo_combustivel'],
                    f"{item['total_litros']:.2f}",
                    f"R$ {item['total_valor']:.2f}"
                ])
        elif report_type == 'consumo_medio_por_veiculo':
            result = view._generate_consumo_medio_por_veiculo(data_inicial, data_final, veiculo)
            report_data = result['report_data']
            report_title = result['report_title']
            headers = ['Placa do Veículo', 'Modelo do Veículo', 'Total Litros', 'Distância Total (KM)', 'Média de Consumo (KM/L)']
            for item in report_data:
                data_for_pdf.append([
                    item['veiculo__placa'],
                    item['veiculo__modelo'],
                    f"{item['total_litros']:.2f}",
                    f"{item['distancia_total']:.2f}",
                    f"{item['media_consumo']:.2f}"
                ])
        elif report_type == 'historico_abastecimento_por_condutor':
            result = view._generate_historico_abastecimento_por_condutor(data_inicial, data_final, condutor)
            report_data = result['report_data']
            report_title = result['report_title']
            headers = ['Condutor', 'Data', 'KM Atual', 'Tipo Combustível', 'Litros', 'Valor Litro', 'Valor Total']
            for item in report_data:
                data_for_pdf.append([
                    item['condutor_nome'],
                    item['data_abastecimento'],
                    str(item['quilometragem_atual']),
                    item['tipo_combustivel'],
                    f"{item['litros']:.2f}",
                    f"R$ {item['valor_litro']:.2f}" if item['valor_litro'] else 'N/A',
                    f"R$ {item['valor_total']:.2f}"
                ])
        elif report_type == 'veiculos_por_status_e_secretaria':
            result = view._generate_veiculos_por_status_e_secretaria(secretaria)
            report_data = result['report_data']
            report_title = result['report_title']
            headers = ['Secretaria', 'Status do Veículo', 'Quantidade']
            for item in report_data:
                data_for_pdf.append([
                    item['secretaria__nome'],
                    item['situacao'],
                    item['count']
                ])
    else:
        return HttpResponse("Erro nos parâmetros do relatório.", status=400)

    # Obter configuração do site para logo e nome do sistema
    configuracao, created = ConfiguracaoSite.objects.get_or_create(pk=1)

    # Definir título do PDF com nome do sistema
    nome_sistema = configuracao.nome_prefeitura or "Sistema de Gestão de Frotas"
    pdf_title = f"{report_title} - {nome_sistema}"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=4*cm,  # Aumentado para acomodar cabeçalho
        bottomMargin=3*cm
    )

    # Definir metadados do PDF
    doc.title = pdf_title
    doc.author = nome_sistema
    doc.subject = report_title

    styles = getSampleStyleSheet()

    # Estilos personalizados para prefeituras
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,  # Centralizado
        textColor=colors.darkblue
    )

    header_style = ParagraphStyle(
        'HeaderInfo',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10,
        alignment=1
    )

    footer_style = ParagraphStyle(
        'FooterInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )

    elements = []

    # Espaçamento inicial para o cabeçalho
    elements.append(Spacer(1, 1*cm))

    # Título do relatório
    elements.append(Paragraph(report_title, title_style))
    elements.append(Spacer(1, 0.3*cm))

    # Data de emissão
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Data de Emissão: {data_emissao}", header_style))

    # Período do relatório
    periodo = f"Período: {data_inicial or 'Não informado'} a {data_final or 'Não informado'}"
    elements.append(Paragraph(periodo, header_style))

    # Filtros aplicados
    filtros = []
    if veiculo:
        filtros.append(f"Veículo: {veiculo.placa}")
    if condutor:
        filtros.append(f"Condutor: {condutor.nome_completo}")
    if secretaria:
        filtros.append(f"Secretaria: {secretaria.nome}")

    if filtros:
        elements.append(Paragraph("Filtros: " + " | ".join(filtros), header_style))

    elements.append(Spacer(1, 1*cm))

    if data_for_pdf:
        # Cores institucionais para prefeituras (verde/azul)
        table_data = [headers] + data_for_pdf
        table = Table(table_data, repeatRows=1)

        # Estilo profissional da tabela
        table_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Corpo da tabela
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),

            # Linhas alternadas
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),

            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ])

        # Aplicar cores alternadas para linhas pares
        for i in range(3, len(table_data), 2):
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)

        table.setStyle(table_style)
        elements.append(table)

        # Resumo estatístico se aplicável
        if report_type in ['abastecimento_por_secretaria', 'gastos_por_tipo_combustivel']:
            def parse_currency(value):
                """Converte string formatada em moeda brasileira para float"""
                if isinstance(value, str):
                    # Remove 'R$ ' e espaços
                    cleaned = value.replace('R$ ', '').replace(' ', '').strip()
                    # Trata formato brasileiro: 9.166,85 -> 9166.85
                    if ',' in cleaned and '.' in cleaned:
                        # Remove pontos (separadores de milhares) e converte vírgula para ponto
                        cleaned = cleaned.replace('.', '').replace(',', '.')
                    elif ',' in cleaned:
                        # Apenas vírgula (decimais): 9166,85 -> 9166.85
                        cleaned = cleaned.replace(',', '.')
                    try:
                        return float(cleaned)
                    except ValueError:
                        return 0.0
                return float(value or 0)

            total_litros = sum(float(row[1]) if row[1] else 0 for row in data_for_pdf)
            total_valor = sum(parse_currency(row[2]) for row in data_for_pdf)

            elements.append(Spacer(1, 1*cm))
            elements.append(Paragraph("RESUMO GERAL", styles['Heading3']))
            elements.append(Paragraph(f"Total de Litros: {total_litros:.2f}", styles['Normal']))
            elements.append(Paragraph(f"Total de Valor: R$ {total_valor:.2f}", styles['Normal']))

    else:
        elements.append(Paragraph("Nenhum dado encontrado para o relatório.", styles['Normal']))

    # Assinatura (pode ser expandido futuramente)
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("_______________________________", footer_style))
    elements.append(Paragraph("Responsável pelo Relatório", footer_style))

    # Construir PDF com cabeçalho e rodapé em todas as páginas
    def page_callback(canvas, doc):
        add_header_and_footer(canvas, doc, configuracao)

    doc.build(elements, onFirstPage=page_callback, onLaterPages=page_callback)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    # Alterado para 'inline' para abrir em nova janela
    response['Content-Disposition'] = f'inline; filename="{pdf_title}.pdf"'
    return response
