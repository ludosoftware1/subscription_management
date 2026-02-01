from django.views.generic import CreateView
from django.http import JsonResponse
from .models import Feedback
from .forms import FeedbackForm

class FeedbackCreateView(CreateView):
    model = Feedback
    form_class = FeedbackForm

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.usuario = self.request.user
        form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors})
