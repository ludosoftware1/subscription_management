from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.static import serve

from apps.tenants.views import DashboardView

from .views import (
    MyPasswordChangeView,
    MyPasswordSetView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DashboardView.as_view(), name="home"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("apps/", include("apps.urls")),
    path("layouts/", include("layouts.urls")),
    path("components/", include("components.urls")),
    path("pages/", include("pages.urls")),
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
    path("account/", include("allauth.urls")),
    path("notificacoes/", include("apps.notificacoes.urls", namespace="notificacoes")),
    path("core/", include("apps.core.urls", namespace="core")),
    path("configuracao/", include("apps.configuracao.urls", namespace="configuracao")),
    path("feedback/", include("apps.feedback.urls", namespace="feedback")),
    path("email/", include("apps.email_app.urls", namespace="email_app")),
    path("tenants/", include("apps.tenants.urls", namespace="tenants")),
    # Anexos (notas fiscais dos pagamentos, logos): servidos pelo Django só a
    # usuários autenticados, inclusive em produção -- o WhiteNoise cuida apenas
    # dos estáticos e não há nginx dedicado para /media/ no container.
    re_path(
        r"^media/(?P<path>.*)$",
        login_required(serve),
        {"document_root": settings.MEDIA_ROOT},
        name="media",
    ),
]

handler403 = "apps.core.views.permission_denied_view"
