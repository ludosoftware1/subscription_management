from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static
from auditlog.registry import auditlog

# Create your models here.
class UserProfile(models.Model):
    """
    Modelo para estender o User padrão do Django com informações adicionais.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    logradouro = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True) # UF
    descricao = models.TextField(blank=True, null=True)
    foto_perfil = models.CharField(max_length=255, default='images/users/avatar-1.svg')
    
    def __str__(self):
        return f'Perfil de {self.user.username}'

    @property
    def get_foto_perfil_url(self):
        if self.foto_perfil:
            return static(self.foto_perfil)
        return static("images/users/avatar-1.svg")

# Registra os modelos para serem auditados pelo django-auditlog
auditlog.register(UserProfile)
auditlog.register(User)
