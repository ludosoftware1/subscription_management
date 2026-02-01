from django.urls import path
from .views import FeedbackCreateView

app_name = 'feedback'

urlpatterns = [
    path('enviar/', FeedbackCreateView.as_view(), name='enviar'),
]
