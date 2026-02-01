from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Feedback(models.Model):
    TIPO_CHOICES = [
        ('SUGESTAO', 'Sugestão de Melhoria'),
        ('ELOGIO', 'Elogio'),
        ('PROBLEMA', 'Relatar um Problema Técnico'),
        ('OUTRO', 'Outro Assunto'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensagem = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    pagina_origem = models.CharField(max_length=255)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.usuario}'
