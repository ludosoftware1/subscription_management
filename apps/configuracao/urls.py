from django.urls import path
from . import views
from . import views_sessions

app_name = 'configuracao'

urlpatterns = [
    path('', views.configuracao_site, name='configuracao_site'),
    path('remover-imagem/<str:campo>/', views.remover_imagem, name='remover_imagem'),
    path('email/', views.configuracao_email, name='configuracao_email'),
    path('email/testar-smtp/', views.testar_conexao_smtp, name='testar_conexao_smtp'),
    path('session_history/', views_sessions.SessionHistoryView.as_view(), name='session_history'),
    path('session_history/<int:pk>/encerrar/', views_sessions.EndUserSessionView.as_view(), name='end_user_session'),
]
