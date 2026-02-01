from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views import View
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.models import UserSession
from django.db.models import Q

User = get_user_model()

class SessionHistoryView(LoginRequiredMixin, ListView):
    """
    View para exibir o histórico de sessões.
    Apenas usuários do grupo 'administrador' podem acessar.
    """
    model = UserSession
    template_name = 'configuracao/session_history.html'
    context_object_name = 'sessions'
    ordering = ['-login_time']
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro de status (ativo/inativo)
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Filtro de usuário (busca por nome ou username)
        user_search = self.request.GET.get('user_search', '').strip()
        if user_search:
            queryset = queryset.filter(
                Q(user__username__icontains=user_search) |
                Q(user__first_name__icontains=user_search) |
                Q(user__last_name__icontains=user_search) |
                Q(user__email__icontains=user_search)
            )
        
        # Filtro de grupo/perfil
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(user__groups__id=group_id)
        
        # Filtro de data (início)
        start_date = self.request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(login_time__date__gte=start_date)
        
        # Filtro de data (fim)
        end_date = self.request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(login_time__date__lte=end_date)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagetitle'] = 'Histórico de Sessões'
        context['title'] = 'Histórico de Sessões de Usuários'
        
        # Adiciona grupos para o filtro
        context['groups'] = Group.objects.all().order_by('name')
        
        # Mantém os valores dos filtros
        context['current_is_active'] = self.request.GET.get('is_active', '')
        context['current_user_search'] = self.request.GET.get('user_search', '')
        context['current_group'] = self.request.GET.get('group', '')
        context['current_start_date'] = self.request.GET.get('start_date', '')
        context['current_end_date'] = self.request.GET.get('end_date', '')
        
        return context

class EndUserSessionView(LoginRequiredMixin, View):
    """
    View para encerrar uma sessão de usuário específica.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        session_pk = kwargs.get('pk')
        user_session = get_object_or_404(UserSession, pk=session_pk)

        if user_session.is_active:
            user_session.end_session()
            messages.success(request, f"Sessão do usuário '{user_session.user.username}' encerrada com sucesso.")
        else:
            messages.info(request, "A sessão já estava inativa.")
        
        return redirect(reverse_lazy('configuracao:session_history'))
