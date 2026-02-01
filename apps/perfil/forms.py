from django import forms
from django.contrib.auth.models import User, Group
from .models import UserProfile
from velzon.forms import UserRegistrationForm

class CustomUserCreationForm(UserRegistrationForm):
    nome_completo = forms.CharField(max_length=150, label="Nome Completo", widget=forms.TextInput(attrs={'class': 'form-control'}))
    cpf = forms.CharField(max_length=14, label="CPF", widget=forms.TextInput(attrs={'class': 'form-control'}))
    data_nascimento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Data de Nascimento")
    telefone = forms.CharField(max_length=20, label="Telefone", widget=forms.TextInput(attrs={'class': 'form-control'}))
    cep = forms.CharField(max_length=10, label="CEP", widget=forms.TextInput(attrs={'class': 'form-control'}))
    rua = forms.CharField(max_length=255, label="Rua", widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero = forms.CharField(max_length=20, label="Número", widget=forms.TextInput(attrs={'class': 'form-control'}))
    complemento = forms.CharField(max_length=100, required=False, label="Complemento", widget=forms.TextInput(attrs={'class': 'form-control'}))
    bairro = forms.CharField(max_length=100, label="Bairro", widget=forms.TextInput(attrs={'class': 'form-control'}))
    cidade = forms.CharField(max_length=100, label="Cidade", widget=forms.TextInput(attrs={'class': 'form-control'}))
    uf = forms.CharField(max_length=2, label="UF", widget=forms.TextInput(attrs={'class': 'form-control'}))

    def save(self, request):
        user = super().save(request)
        user.username = self.cleaned_data['email']
        
        # Divide o nome completo em nome e sobrenome
        nome_completo = self.cleaned_data.get('nome_completo', '').strip()
        if ' ' in nome_completo:
            user.first_name, user.last_name = nome_completo.split(' ', 1)
        else:
            user.first_name = nome_completo
            user.last_name = ''
        user.save()
        
        # Em vez de criar, atualiza o perfil que pode ter sido criado por um signal
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.cpf = self.cleaned_data.get('cpf')
        profile.data_nascimento = self.cleaned_data.get('data_nascimento')
        profile.telefone = self.cleaned_data.get('telefone')
        profile.cep = self.cleaned_data.get('cep')
        profile.logradouro = self.cleaned_data.get('rua')
        profile.numero = self.cleaned_data.get('numero')
        profile.complemento = self.cleaned_data.get('complemento')
        profile.bairro = self.cleaned_data.get('bairro')
        profile.cidade = self.cleaned_data.get('cidade')
        profile.uf = self.cleaned_data.get('uf')
        profile.save()

        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    email = forms.EmailField(required=False, label="Endereço de E-mail")

    class Meta:
        model = UserProfile
        fields = ['cpf', 'data_nascimento', 'telefone', 'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'descricao', 'foto_perfil']
        labels = {
            'cpf': 'CPF',
            'data_nascimento': 'Data de Nascimento',
            'telefone': 'Telefone',
            'cep': 'CEP',
            'logradouro': 'Logradouro',
            'numero': 'Número',
            'complemento': 'Complemento',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'uf': 'Estado (UF)',
            'descricao': 'Descrição',
            'foto_perfil': 'Foto do Perfil',
        }
        widgets = {
            'foto_perfil': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
