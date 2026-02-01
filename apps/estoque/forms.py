from django import forms
from .models import UnidadeMedida, CategoriaProduto, Produto, MovimentacaoEstoque

class UnidadeMedidaForm(forms.ModelForm):
    class Meta:
        model = UnidadeMedida
        fields = ['nome', 'sigla', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da unidade'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg, L, m, un'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição opcional'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CategoriaProdutoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da categoria'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição da categoria'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['codigo', 'nome', 'descricao', 'categoria', 'unidade_medida',
                 'quantidade_atual', 'quantidade_minima', 'localizacao', 'observacoes', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código do produto'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do produto'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do produto'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidade_medida': forms.Select(attrs={'class': 'form-select'}),
            'quantidade_atual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade_minima': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Localização no almoxarifado'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações adicionais'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas unidades ativas
        self.fields['unidade_medida'].queryset = UnidadeMedida.objects.filter(ativo=True)
        # Filtrar apenas categorias ativas
        self.fields['categoria'].queryset = CategoriaProduto.objects.filter(ativo=True)

class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'quantidade', 'observacoes']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações da movimentação'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas produtos ativos
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        tipo = cleaned_data.get('tipo')
        quantidade = cleaned_data.get('quantidade')

        if produto and tipo and quantidade:
            if tipo == 'saida' and produto.quantidade_atual < quantidade:
                raise forms.ValidationError(
                    f"Quantidade insuficiente em estoque. Disponível: {produto.quantidade_atual} {produto.unidade_medida}"
                )

        return cleaned_data
