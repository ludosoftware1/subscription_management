import io

from django.core.management import CommandError, call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse


class CoreLoginTest(TestCase):
    def test_login_page_status_code(self):
        """
        Verifica se a página de login retorna o código de status 200 (OK).
        """
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)


class VerificarBancoTest(TransactionTestCase):
    def _rodar(self):
        saida = io.StringIO()
        call_command("verificar_banco", stdout=saida)
        return saida.getvalue()

    def test_banco_do_painel_passa(self):
        self.assertIn("OK para o painel", self._rodar())

    def test_recusa_banco_do_syndoc(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE users_client (id integer)")
        try:
            with self.assertRaisesMessage(CommandError, "é o do SynDoc"):
                self._rodar()
        finally:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE users_client")

    def test_recusa_auth_registrado_sem_auth_user(self):
        # Simula o schema public do django-tenants: migration do auth registrada, tabela ausente.
        tabelas = set(connection.introspection.table_names())
        self.assertIn("auth_user", tabelas)
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE auth_user RENAME TO auth_user_bkp")
        try:
            with self.assertRaisesMessage(CommandError, "auth_user não existe"):
                self._rodar()
        finally:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE auth_user_bkp RENAME TO auth_user")
