from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

class Notificacao(models.Model):
    """
    Modelo para representar uma notificação para um usuário.
    """
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificacoes')
    titulo = models.CharField(max_length=255)
    mensagem = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data de criação")
    lida = models.BooleanField(default=False)

    # Campos para um link genérico para qualquer outro objeto do Django
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'

    def __str__(self):
        return self.titulo

    def clean(self):
        """
        Prevents a notification from pointing to itself as the content_object.
        """
        super().clean()
        if self.content_type and self.object_id:
            notification_ct = ContentType.objects.get_for_model(self.__class__)
            if self.content_type == notification_ct and self.object_id == self.id:
                raise ValidationError({'content_object': 'A notification cannot point to itself.'})

    def get_absolute_url(self):
        """
        Retorna a URL para o objeto de conteúdo relacionado, com lógica customizada
        para direcionar o usuário para a view correta (cidadão ou gestor).
        """
        from django.urls import reverse

        if self.content_object:
            # Lógica padrão para gestores ou outros objetos
            if hasattr(self.content_object, 'get_absolute_url'):
                return self.content_object.get_absolute_url()

        # Fallback
        return ""
