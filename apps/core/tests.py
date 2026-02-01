from django.test import TestCase
from django.urls import reverse

class CoreLoginTest(TestCase):
    def test_login_page_status_code(self):
        """
        Verifica se a página de login retorna o código de status 200 (OK).
        """
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)