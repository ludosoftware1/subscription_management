from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'usuario', 'pagina_origem', 'data_criacao')
    list_filter = ('tipo', 'data_criacao')
    search_fields = ('usuario__username', 'mensagem')
