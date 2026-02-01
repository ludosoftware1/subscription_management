from django.contrib import admin
from django.urls import path,include
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings
from .views import (
    MyPasswordChangeView,
    MyPasswordSetView
)
from pages.views import pages_starter

urlpatterns = [
    path('admin/', admin.site.urls),
    # Dashboard - Redirect to Estoque Dashboard
    path('', login_required(lambda request: redirect('estoque:dashboard')), name='home'),
    # Apps
    path('apps/',include('apps.urls')),
    # Layouts
    path('layouts/',include('layouts.urls')),
    # Components
    path('components/',include('components.urls')),
    # Pages
    path('pages/',include('pages.urls')),

    path(
        "account/password/change/",
        login_required(MyPasswordChangeView.as_view()),
        name="account_change_password",
    ),
    path(
        "account/password/set/",
        login_required(MyPasswordSetView.as_view()),
        name="account_set_password",
    ),
    # All Auth
    path('account/', include('allauth.urls')),

    # Notificações
    path('notificacoes/', include('apps.notificacoes.urls', namespace='notificacoes')),

    # Core
    path('core/', include('apps.core.urls', namespace='core')),

    # Configuração
    path('configuracao/', include('apps.configuracao.urls', namespace='configuracao')),

    # Feedback
    path('feedback/', include('apps.feedback.urls', namespace='feedback')),

    # Email
    path('email/', include('apps.email_app.urls', namespace='email_app')),

    # Estoque
    path('estoque/', include('apps.estoque.urls', namespace='estoque')),

    # Relatórios
    path('relatorios/', include('apps.relatorios.urls', namespace='relatorios')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'apps.core.views.permission_denied_view'
