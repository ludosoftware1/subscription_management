from django.urls import path
from . import views

app_name = 'notificacoes'

urlpatterns = [
    path('api/nao-lidas/', views.api_notificacoes_nao_lidas, name='api_nao_lidas'),
    path('api/marcar-como-lida/', views.api_marcar_como_lida, name='api_marcar_como_lida'),
]
