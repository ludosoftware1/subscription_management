from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from auditlog.registry import auditlog

User = get_user_model()

class UnidadeMedida(models.Model):
    """Unidades de medida para produtos"""
    nome = models.CharField("Nome", max_length=50, unique=True)
    sigla = models.CharField("Sigla", max_length=10, unique=True, help_text="Ex: kg, L, m, un")
    descricao = models.CharField("Descrição", max_length=100, blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

class CategoriaProduto(models.Model):
    """Categoria para organizar os produtos"""
    nome = models.CharField("Nome", max_length=100, unique=True)
    descricao = models.TextField("Descrição", blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produtos"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Produto(models.Model):
    """Modelo para produtos/itens do almoxarifado"""
    codigo = models.CharField("Código", max_length=50, unique=True)
    nome = models.CharField("Nome", max_length=200)
    descricao = models.TextField("Descrição", blank=True)
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria")

    unidade_medida = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, verbose_name="Unidade de Medida")
    quantidade_atual = models.DecimalField("Quantidade Atual", max_digits=10, decimal_places=2, default=0)
    quantidade_minima = models.DecimalField("Quantidade Mínima", max_digits=10, decimal_places=2, default=0)

    localizacao = models.CharField("Localização", max_length=100, blank=True, help_text="Onde o produto está armazenado")
    observacoes = models.TextField("Observações", blank=True)

    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo"""
        return self.quantidade_atual <= self.quantidade_minima

    def atualizar_quantidade(self, quantidade, tipo_movimentacao, usuario, observacoes=""):
        """Atualiza a quantidade e cria movimentação"""
        if tipo_movimentacao == 'entrada':
            self.quantidade_atual += quantidade
        elif tipo_movimentacao == 'saida':
            if self.quantidade_atual < quantidade:
                raise ValueError("Quantidade insuficiente em estoque")
            self.quantidade_atual -= quantidade
        else:
            raise ValueError("Tipo de movimentação inválido")

        self.save()

        # Criar registro de movimentação
        MovimentacaoEstoque.objects.create(
            produto=self,
            tipo=tipo_movimentacao,
            quantidade=quantidade,
            quantidade_anterior=self.quantidade_atual - quantidade if tipo_movimentacao == 'entrada' else self.quantidade_atual + quantidade,
            quantidade_atual=self.quantidade_atual,
            usuario=usuario,
            observacoes=observacoes
        )

        return self

class MovimentacaoEstoque(models.Model):
    """Registro de movimentações de entrada e saída"""

    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name="Produto")
    tipo = models.CharField("Tipo", max_length=10, choices=TIPO_CHOICES)
    quantidade = models.DecimalField("Quantidade Movimentada", max_digits=10, decimal_places=2)
    quantidade_anterior = models.DecimalField("Quantidade Anterior", max_digits=10, decimal_places=2)
    quantidade_atual = models.DecimalField("Quantidade Atual", max_digits=10, decimal_places=2)

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    data_movimentacao = models.DateTimeField("Data da Movimentação", default=timezone.now)
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data_movimentacao']

    def __str__(self):
        return f"{self.tipo.title()} - {self.produto.nome} ({self.quantidade})"

# Registrar modelos para auditoria
auditlog.register(Produto)
auditlog.register(MovimentacaoEstoque)
auditlog.register(CategoriaProduto)
