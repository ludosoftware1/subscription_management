from django.urls import path
from .views import RelatorioSelectionView, CentroRelatoriosView, export_report_to_excel, export_report_to_pdf

app_name = 'relatorios'

urlpatterns = [
    path('', RelatorioSelectionView.as_view(), name='report_selection'),
    path('centro/', CentroRelatoriosView.as_view(), name='centro_relatorios'),
    path('export/excel/', export_report_to_excel, name='export_excel'),
    path('export/pdf/', export_report_to_pdf, name='export_pdf'),
]
