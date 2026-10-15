"""Recusa migrar num banco que não é o deste painel.

O painel precisa de um banco PRÓPRIO. Apontar ``POSTGRES_DB`` para o banco do
UltraDoc é um erro fácil (mesmo servidor, mesmo usuário ``ultradoc``) e grave:
o ``migrate`` criaria as tabelas do painel no schema ``public`` do UltraDoc.

Lá o ``django.contrib.auth`` é app de tenant: o django-tenants REGISTRA as
migrations do ``auth`` em ``public.django_migrations``, mas só cria
``auth_user`` dentro do schema de cada cliente. O ``migrate`` deste painel então
pula o ``auth`` ("já aplicado") e falha com
``relation "auth_user" does not exist`` -- depois de já ter criado as tabelas que
não dependem dele. Este comando roda ANTES do ``migrate`` no entrypoint.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# Tabelas do app ``users`` do UltraDoc (Client/Domain do django-tenants).
TABELAS_ULTRADOC = ("users_client", "users_domain")


class Command(BaseCommand):
    help = "Aborta se o banco configurado for o do UltraDoc ou estiver com o histórico de migrations inconsistente."

    def handle(self, *args, **options):
        banco = connection.settings_dict.get("NAME")
        tabelas = set(connection.introspection.table_names())

        do_ultradoc = sorted(t for t in TABELAS_ULTRADOC if t in tabelas)
        if do_ultradoc:
            raise CommandError(
                f"O banco '{banco}' é o do UltraDoc (tem {', '.join(do_ultradoc)}). "
                "O painel precisa de um banco próprio: crie um (ex.: "
                "`sudo -u postgres createdb --owner=ultradoc subscription_management`), "
                "ajuste POSTGRES_DB no .env e recrie o container."
            )

        if "django_migrations" in tabelas and "auth_user" not in tabelas:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM django_migrations WHERE app = %s LIMIT 1", ["auth"])
                if cursor.fetchone():
                    raise CommandError(
                        f"O banco '{banco}' registra as migrations do auth como aplicadas, mas a tabela "
                        "auth_user não existe. Ele provavelmente pertence a outro sistema "
                        "(django-tenants). Use um banco próprio para o painel em POSTGRES_DB."
                    )

        self.stdout.write(self.style.SUCCESS(f"Banco '{banco}' OK para o painel."))
