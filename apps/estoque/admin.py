from django.contrib import admin
from .models import UnidadeMedida, CategoriaProduto, Produto, MovimentacaoEstoque

@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'sigla', 'descricao')
    ordering = ('nome',)

@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    ordering = ('nome',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'categoria', 'unidade_medida', 'quantidade_atual', 'quantidade_minima', 'ativo', 'estoque_baixo')
    list_filter = ('ativo', 'categoria', 'unidade_medida')
    search_fields = ('codigo', 'nome', 'descricao')
    ordering = ('nome',)
    readonly_fields = ('criado_em', 'atualizado_em')

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tipo', 'quantidade', 'usuario', 'data_movimentacao')
    list_filter = ('tipo', 'data_movimentacao', 'usuario')
    search_fields = ('produto__nome', 'produto__codigo', 'observacoes')
    ordering = ('-data_movimentacao',)
    readonly_fields = ('data_movimentacao',)
