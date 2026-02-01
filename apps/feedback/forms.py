from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['tipo', 'mensagem', 'pagina_origem']
        widgets = {
            'pagina_origem': forms.HiddenInput(),
        }
