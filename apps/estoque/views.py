from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from .models import UnidadeMedida, CategoriaProduto, Produto, MovimentacaoEstoque
from .forms import UnidadeMedidaForm, CategoriaProdutoForm, ProdutoForm, MovimentacaoEstoqueForm

# ==================== UNIDADE MEDIDA VIEWS ====================

class UnidadeMedidaListView(LoginRequiredMixin, ListView):
    model = UnidadeMedida
    template_name = 'estoque/unidade_list.html'
    context_object_name = 'unidades'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(sigla__icontains=search) |
                Q(descricao__icontains=search)
            )
        return queryset.order_by('nome')

class UnidadeMedidaCreateView(LoginRequiredMixin, CreateView):
    model = UnidadeMedida
    form_class = UnidadeMedidaForm
    template_name = 'estoque/unidade_form.html'
    success_url = reverse_lazy('estoque:unidade_list')

    def form_valid(self, form):
        messages.success(self.request, 'Unidade de medida criada com sucesso!')
        return super().form_valid(form)

class UnidadeMedidaUpdateView(LoginRequiredMixin, UpdateView):
    model = UnidadeMedida
    form_class = UnidadeMedidaForm
    template_name = 'estoque/unidade_form.html'
    success_url = reverse_lazy('estoque:unidade_list')

    def form_valid(self, form):
        messages.success(self.request, 'Unidade de medida atualizada com sucesso!')
        return super().form_valid(form)

class UnidadeMedidaDeleteView(LoginRequiredMixin, DeleteView):
    model = UnidadeMedida
    template_name = 'estoque/unidade_confirm_delete.html'
    success_url = reverse_lazy('estoque:unidade_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Unidade de medida excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

# ==================== CATEGORIA PRODUTO VIEWS ====================

class CategoriaProdutoListView(LoginRequiredMixin, ListView):
    model = CategoriaProduto
    template_name = 'estoque/categoria_list.html'
    context_object_name = 'categorias'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(descricao__icontains=search)
            )
        return queryset.order_by('nome')

class CategoriaProdutoCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaProduto
    form_class = CategoriaProdutoForm
    template_name = 'estoque/categoria_form.html'
    success_url = reverse_lazy('estoque:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoria criada com sucesso!')
        return super().form_valid(form)

class CategoriaProdutoUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaProduto
    form_class = CategoriaProdutoForm
    template_name = 'estoque/categoria_form.html'
    success_url = reverse_lazy('estoque:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada com sucesso!')
        return super().form_valid(form)

class CategoriaProdutoDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaProduto
    template_name = 'estoque/categoria_confirm_delete.html'
    success_url = reverse_lazy('estoque:categoria_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Categoria excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

# ==================== PRODUTO VIEWS ====================

class ProdutoListView(LoginRequiredMixin, ListView):
    model = Produto
    template_name = 'estoque/produto_list.html'
    context_object_name = 'produtos'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        categoria = self.request.GET.get('categoria')
        status = self.request.GET.get('status')

        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(nome__icontains=search) |
                Q(descricao__icontains=search)
            )

        if categoria:
            queryset = queryset.filter(categoria_id=categoria)

        if status == 'baixo':
            queryset = queryset.filter(quantidade_atual__lte=models.F('quantidade_minima'))
        elif status == 'ativo':
            queryset = queryset.filter(ativo=True)
        elif status == 'inativo':
            queryset = queryset.filter(ativo=False)

        return queryset.select_related('categoria').order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaProduto.objects.filter(ativo=True)
        context['estoque_baixo_count'] = Produto.objects.filter(
            quantidade_atual__lte=models.F('quantidade_minima'),
            ativo=True
        ).count()
        return context

class ProdutoDetailView(LoginRequiredMixin, DetailView):
    model = Produto
    template_name = 'estoque/produto_detail.html'
    context_object_name = 'produto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movimentacoes'] = MovimentacaoEstoque.objects.filter(
            produto=self.object
        ).select_related('usuario').order_by('-data_movimentacao')[:10]
        return context

class ProdutoCreateView(LoginRequiredMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'estoque/produto_form.html'
    success_url = reverse_lazy('estoque:produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto criado com sucesso!')
        return super().form_valid(form)

class ProdutoUpdateView(LoginRequiredMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'estoque/produto_form.html'
    success_url = reverse_lazy('estoque:produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado com sucesso!')
        return super().form_valid(form)

class ProdutoDeleteView(LoginRequiredMixin, DeleteView):
    model = Produto
    template_name = 'estoque/produto_confirm_delete.html'
    success_url = reverse_lazy('estoque:produto_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Produto excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

# ==================== MOVIMENTACAO ESTOQUE VIEWS ====================

class MovimentacaoEstoqueListView(LoginRequiredMixin, ListView):
    model = MovimentacaoEstoque
    template_name = 'estoque/movimentacao_list.html'
    context_object_name = 'movimentacoes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        tipo = self.request.GET.get('tipo')
        data_inicial = self.request.GET.get('data_inicial')
        data_final = self.request.GET.get('data_final')

        if search:
            queryset = queryset.filter(
                Q(produto__codigo__icontains=search) |
                Q(produto__nome__icontains=search) |
                Q(observacoes__icontains=search)
            )

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if data_inicial:
            queryset = queryset.filter(data_movimentacao__date__gte=data_inicial)

        if data_final:
            queryset = queryset.filter(data_movimentacao__date__lte=data_final)

        return queryset.select_related('produto', 'usuario').order_by('-data_movimentacao')

class MovimentacaoEstoqueCreateView(LoginRequiredMixin, CreateView):
    model = MovimentacaoEstoque
    form_class = MovimentacaoEstoqueForm
    template_name = 'estoque/movimentacao_form.html'
    success_url = reverse_lazy('estoque:movimentacao_list')

    def form_valid(self, form):
        form.instance.usuario = self.request.user

        # Atualizar quantidade do produto
        produto = form.instance.produto
        quantidade = form.instance.quantidade
        tipo = form.instance.tipo

        try:
            produto.atualizar_quantidade(quantidade, tipo, self.request.user, form.instance.observacoes)
            messages.success(self.request, f'Movimentação de {tipo} registrada com sucesso!')
            return super().form_valid(form)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

# ==================== DASHBOARD VIEW ====================

class EstoqueDashboardView(LoginRequiredMixin, ListView):
    model = Produto
    template_name = 'estoque/dashboard.html'
    context_object_name = 'produtos'

    def get_queryset(self):
        return Produto.objects.filter(ativo=True).select_related('categoria').order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Estatísticas gerais
        context['total_produtos'] = Produto.objects.filter(ativo=True).count()
        context['produtos_baixo_estoque'] = Produto.objects.filter(
            quantidade_atual__lte=models.F('quantidade_minima'),
            ativo=True
        )
        context['total_categorias'] = CategoriaProduto.objects.filter(ativo=True).count()

        # Movimentações recentes
        context['movimentacoes_recentes'] = MovimentacaoEstoque.objects.select_related(
            'produto', 'usuario'
        ).order_by('-data_movimentacao')[:10]

        # Produtos com estoque baixo
        context['estoque_baixo'] = Produto.objects.filter(
            quantidade_atual__lte=models.F('quantidade_minima'),
            ativo=True
        ).select_related('categoria')[:10]

        return context

# ==================== AJAX VIEWS ====================

def get_produto_info(request, produto_id):
    """Retorna informações do produto via AJAX"""
    try:
        produto = Produto.objects.get(id=produto_id, ativo=True)
        data = {
            'id': produto.id,
            'codigo': produto.codigo,
            'nome': produto.nome,
            'quantidade_atual': str(produto.quantidade_atual),
            'unidade_medida': produto.unidade_medida,
            'estoque_baixo': produto.estoque_baixo,
        }
        return JsonResponse(data)
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)
