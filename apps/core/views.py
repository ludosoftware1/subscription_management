from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.views import View
from django.http import HttpResponse, HttpResponseForbidden # Adicionar import para HttpResponse e HttpResponseForbidden

class DownloadDocumentoView(View):
    def get(self, request, pk):
        # Implementação temporária para evitar erro
        return HttpResponse(f"Download do documento {pk}")

class VerificarCodigoView(View):
    def get(self, request, codigo):
        # Implementação temporária para evitar erro
        return HttpResponse(f"Verificando código {codigo}")

def permission_denied_view(request, exception):
    return HttpResponseForbidden("403 Forbidden: Você não tem permissão para acessar esta página.")
