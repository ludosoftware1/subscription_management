from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from velzon.adapters import MyAccountAdapter
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.perfil.forms import UserProfileForm, CustomUserCreationForm
from apps.configuracao.models import AuditLogEntry # Alterado de LogEntry para nosso proxy
from .forms import AuditLogFilterForm
from django.core.paginator import Paginator
from datetime import timedelta
from django.utils import timezone
from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.views import View

# Create your views here.
def pages_profile_view(request):
    user = request.user
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Busca as atividades do usuário logado por período
    activities_today = AuditLogEntry.objects.filter(
        actor=user, timestamp__date=today
    ).select_related('content_type').order_by('-timestamp')

    activities_weekly = AuditLogEntry.objects.filter(
        actor=user, timestamp__date__gte=start_of_week
    ).select_related('content_type').order_by('-timestamp')

    activities_monthly = AuditLogEntry.objects.filter(
        actor=user, timestamp__date__gte=start_of_month
    ).select_related('content_type').order_by('-timestamp')

    context = {
        'activities_today': activities_today,
        'activities_weekly': activities_weekly,
        'activities_monthly': activities_monthly,
    }
    return render(request, "pages/pages-profile.html", context)

@login_required
def pages_profile_settings_view(request):
    user_profile = request.user.profile
    form = UserProfileForm(instance=user_profile) # Inicializa o form para GET

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('pages:pages.profile_settings') # Redireciona e encerra

    # Lista de avatares para exibir no template
    avatares = [
        "images/users/avatar-1.svg",
        "images/users/avatar-2.svg",
        "images/users/avatar-3.svg",
        "images/users/avatar-4.svg",
        "images/users/avatar-5.svg",
        "images/users/avatar-6.svg",
        "images/users/avatar-7.svg",
        "images/users/avatar-8.svg",
        "images/users/avatar-9.svg",
        "images/users/avatar-10.svg",
        "images/users/avatar-11.svg",
        "images/users/avatar-12.svg",
    ]

    contexto = {
        'form': form,
        'avatares': avatares,
    }
    return render(request, "pages/pages-profile-settings.html", contexto)

from django.utils.decorators import method_decorator

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

@method_decorator(login_required, name='dispatch')
class AuditTrailView(LoginRequiredMixin, View):
    def get(self, request):
        """
        Exibe a trilha de auditoria com filtros e paginação.
        """
        # Exclui registros de atualização de 'last_login' do usuário
        user_content_type = ContentType.objects.get_for_model(get_user_model())
        log_list = AuditLogEntry.objects.select_related('actor', 'content_type').exclude(
            Q(action=1) & # 1 = UPDATE
            Q(content_type=user_content_type) &
            Q(changes_text__iregex=r'^{\s*"last login":\s*\[.*\]\s*}$')
        ).order_by('-timestamp')

        form = AuditLogFilterForm(request.GET)

        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            user = form.cleaned_data.get('user')
            action = form.cleaned_data.get('action')

            if start_date:
                log_list = log_list.filter(timestamp__date__gte=start_date)
            if end_date:
                # Adiciona 1 dia para incluir o dia inteiro na busca
                log_list = log_list.filter(timestamp__date__lte=end_date)
            if user:
                log_list = log_list.filter(actor=user)
            if action:
                log_list = log_list.filter(action=action)

        paginator = Paginator(log_list, 25)  # 25 logs por página
        page_number = request.GET.get('page')
        log_entries = paginator.get_page(page_number)

        context = {
            'log_entries': log_entries,
            'filter_form': form,
        }
        return render(request, 'pages/audit_trail.html', context)

audit_trail_view = AuditTrailView.as_view()

@login_required
def lock_screen(request):
    """Bloqueia a sessão do usuário."""
    request.session['is_locked'] = True
    return redirect('pages:unlock_screen')

@login_required
def unlock_screen(request):
    """Exibe a tela de bloqueio e processa o desbloqueio."""
    if not request.session.get('is_locked'):
        return redirect('home') # Redireciona para o dashboard se não estiver bloqueado

    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            # Senha correta, desbloqueia a sessão
            del request.session['is_locked']
            return redirect('home')
        else:
            messages.error(request, 'Senha incorreta. Tente novamente.')
    
    return render(request, 'pages/authentication/auth-lockscreen-basic.html')

# Authentication
def authentication_signin_basic(request):
    return render(request, 'pages/authentication/auth-signin-basic.html')

def authentication_signin_cover(request):
    return render(request, 'pages/authentication/auth-signin-cover.html')

def authentication_signup_basic(request):
    return render(request, 'pages/authentication/auth-signup-basic.html')

def authentication_signup_cover(request):
    return render(request, 'pages/authentication/auth-signup-cover.html')

def authentication_pass_reset_basic(request):
    return render(request, 'pages/authentication/auth-pass-reset-basic.html')

def authentication_pass_reset_cover(request):
    return render(request, 'pages/authentication/auth-pass-reset-cover.html')

def authentication_lockscreen_basic(request):
    return render(request, 'pages/authentication/auth-lockscreen-basic.html')

def authentication_lockscreen_cover(request):
    return render(request, 'pages/authentication/auth-lockscreen-cover.html')

def authentication_logout_basic(request):
    return render(request, 'pages/authentication/auth-logout-basic.html')

def authentication_logout_cover(request):
    return render(request, 'pages/authentication/auth-logout-cover.html')

def authentication_success_msg_basic(request):
    return render(request, 'pages/authentication/auth-success-msg-basic.html')

def authentication_success_msg_cover(request):
    return render(request, 'pages/authentication/auth-success-msg-cover.html')

def authentication_twostep_basic(request):
    return render(request, 'pages/authentication/auth-twostep-basic.html')

def authentication_twostep_cover(request):
    return render(request, 'pages/authentication/auth-twostep-cover.html')

def authentication_404_basic(request):
    return render(request, 'pages/authentication/auth-404-basic.html')

def authentication_404_cover(request):
    return render(request, 'pages/authentication/auth-404-cover.html')

def authentication_404_alt(request):
    return render(request, 'pages/authentication/auth-404-alt.html')

def authentication_500(request):
    return render(request, 'pages/authentication/auth-500.html')

def authentication_pass_change_basic(request):
    return render(request, 'pages/authentication/auth-pass-change-basic.html')

def authentication_pass_change_cover(request):
    return render(request, 'pages/authentication/auth-pass-change-cover.html')

def authentication_offline(request):
    return render(request, 'pages/authentication/auth-offline.html')

# Pages
def pages_starter(request):
    return render(request, 'pages/pages-starter.html')

def pages_team(request):
    return render(request, 'pages/pages-team.html')

def pages_timeline(request):
    return render(request, 'pages/pages-timeline.html')

def pages_faqs(request):
    return render(request, 'pages/pages-faqs.html')

def pages_pricing(request):
    return render(request, 'pages/pages-pricing.html')

def pages_gallery(request):
    return render(request, 'pages/pages-gallery.html')

def pages_maintenance(request):
    return render(request, 'pages/pages-maintenance.html')

def pages_coming_soon(request):
    return render(request, 'pages/pages-coming-soon.html')

def pages_sitemap(request):
    return render(request, 'pages/pages-sitemap.html')

def pages_search_results(request):
    return render(request, 'pages/pages-search-results.html')

def pages_privacy_policy(request):
    return render(request, 'pages/pages-privacy-policy.html')

def pages_terms_conditions(request):
    return render(request, 'pages/pages-terms-conditions.html')

def pages_blog_grid(request):
    return render(request, 'pages/blog/pages-blog-grid.html')

def pages_blog_list(request):
    return render(request, 'pages/blog/pages-blog-list.html')

def pages_blog_overview(request):
    return render(request, 'pages/blog/pages-blog-overview.html')

def pages_landing(request):
    return render(request, 'pages/landings/pages-landing.html')

def pages_nft_landing(request):
    return render(request, 'pages/landings/pages-nft-landing.html')

def pages_job_landing(request):
    return render(request, 'pages/landings/pages-job-landing.html')

def solicitar_evento_instrucoes(request):
    """
    Exibe a página de instruções para solicitar um evento.
    """
    return render(request, 'pages/solicitar-evento-instrucoes.html')

def solicitar_evento_cadastro(request):
    """
    Exibe e processa o formulário de cadastro para solicitação de evento.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid(): 
            try:
                with transaction.atomic():
                    user = form.save(request)
                    # O login é tratado automaticamente pelo allauth (form.save)
                    messages.success(request, 'Cadastro realizado com sucesso!')
                    
                    # Usa o adapter para obter a URL de redirecionamento correta
                    adapter = MyAccountAdapter()
                    redirect_url = adapter.get_login_redirect_url(request)
                    return redirect(redirect_url)
            except Exception as e: messages.error(request, f"Ocorreu um erro inesperado durante o cadastro: {e}")
        else:
            # Log de depuração para ver os erros do formulário
            import logging
            logging.basicConfig(level=logging.DEBUG)
            logging.debug(f"Form errors: {form.errors.as_json()}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'pages/solicitar-evento-cadastro.html', {'form': form})

def check_email_availability(request):
    """
    Verifica se um e-mail já está cadastrado (via AJAX).
    """
    email = request.GET.get('email', None)
    if email is None:
        return JsonResponse({'error': 'Email not provided'}, status=400)

    User = get_user_model()
    is_taken = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'is_taken': is_taken})

@login_required
def instrucoes_sistema(request):
    """
    Exibe a página de instruções do sistema com guias ilustrativos.
    """
    return render(request, 'pages/instrucoes-sistema.html')
