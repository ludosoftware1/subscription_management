import uuid
from django.db import models

class EmailLog(models.Model):
    internal_id = models.UUIDField(editable=False, unique=True, null=True, blank=True, help_text="ID interno para rastreamento antes do callback")
    job_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="ID do job retornado pela API no callback")
    to = models.JSONField(help_text="Lista de destinatários")
    sender = models.CharField(max_length=255, help_text="Remetente do e-mail")
    subject = models.CharField(max_length=255, help_text="Assunto do e-mail")
    body = models.TextField(help_text="Corpo do e-mail")
    status = models.CharField(max_length=50, default='pending', help_text="Status do envio: pending, success, failed")
    details = models.TextField(blank=True, null=True, help_text="Detalhes do retorno da API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.status}"
