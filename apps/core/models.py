from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from auditlog.registry import auditlog

User = get_user_model()

class UserSession(models.Model):
    """
    Registra o histórico de sessões de login dos usuários.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', verbose_name="Usuário")
    session_key = models.CharField(max_length=40, unique=True, null=True, blank=True, verbose_name="Chave da Sessão")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    login_time = models.DateTimeField(auto_now_add=True, verbose_name="Hora do Login")
    logout_time = models.DateTimeField(null=True, blank=True, verbose_name="Hora do Logout")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Sessão do Usuário"
        verbose_name_plural = "Sessões dos Usuários"
        ordering = ['-login_time']

    def __str__(self):
        return f"Sessão de {self.user.username} em {self.login_time.strftime('%d/%m/%Y %H:%M')}"

    def end_session(self):
        """Marca a sessão como inativa e registra a hora do logout."""
        if self.is_active:
            self.is_active = False
            self.logout_time = timezone.now()
            self.save()

    def get_duration(self):
        """Calcula a duração da sessão."""
        if self.logout_time and self.login_time:
            return self.logout_time - self.login_time
        return None

    @property
    def session_duration(self):
        """Propriedade para acessar a duração da sessão."""
        return self.get_duration()
    
auditlog.register(UserSession)
