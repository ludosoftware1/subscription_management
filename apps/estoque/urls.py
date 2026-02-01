from django.urls import path
from . import views

app_name = 'estoque'

urlpatterns = [
    # Dashboard
    path('', views.EstoqueDashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.EstoqueDashboardView.as_view(), name='dashboard'),

    # Unidades de Medida
    path('unidades/', views.UnidadeMedidaListView.as_view(), name='unidade_list'),
    path('unidades/adicionar/', views.UnidadeMedidaCreateView.as_view(), name='unidade_create'),
    path('unidades/<int:pk>/editar/', views.UnidadeMedidaUpdateView.as_view(), name='unidade_update'),
    path('unidades/<int:pk>/excluir/', views.UnidadeMedidaDeleteView.as_view(), name='unidade_delete'),

    # Categorias
    path('categorias/', views.CategoriaProdutoListView.as_view(), name='categoria_list'),
    path('categorias/adicionar/', views.CategoriaProdutoCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaProdutoUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/excluir/', views.CategoriaProdutoDeleteView.as_view(), name='categoria_delete'),

    # Produtos
    path('produtos/', views.ProdutoListView.as_view(), name='produto_list'),
    path('produtos/adicionar/', views.ProdutoCreateView.as_view(), name='produto_create'),
    path('produtos/<int:pk>/', views.ProdutoDetailView.as_view(), name='produto_detail'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_update'),
    path('produtos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto_delete'),

    # Movimentações
    path('movimentacoes/', views.MovimentacaoEstoqueListView.as_view(), name='movimentacao_list'),
    path('movimentacoes/adicionar/', views.MovimentacaoEstoqueCreateView.as_view(), name='movimentacao_create'),

    # AJAX
    path('api/produto/<int:produto_id>/info/', views.get_produto_info, name='produto_info'),
]
