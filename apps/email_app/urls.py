from django.urls import path
from . import views

app_name = 'email'

urlpatterns = [
    path('test-email/', views.test_email_page, name='test_email_page'),
    path('email-callback/<uuid:internal_id>/', views.email_callback, name='email_callback'),
    path('resend-email/<int:log_id>/', views.resend_email, name='resend_email'),
]
