"""Prepara e confere o banco antes do ``migrate`` (roda no entrypoint).

O painel não pode gravar no schema ``public`` do SynDoc: lá ficam
``users_client``/``users_domain`` (o cadastro de todos os clientes) e o
histórico de migrations do django-tenants. Duas formas válidas de configurar:

1. Banco exclusivo do painel (``POSTGRES_DB`` próprio, ``POSTGRES_SCHEMA`` vazio).
2. Mesmo banco do SynDoc com ``POSTGRES_SCHEMA`` (ex.: ``painel_assinaturas``):
   este comando cria o schema e o ``search_path`` da conexão faz todas as
   tabelas do painel irem para ele, sem tocar no ``public``.

Sem uma das duas, apontar para o banco do SynDoc fazia o ``migrate`` falhar com
``relation "auth_user" does not exist``: no SynDoc o ``auth`` é app de tenant, o
django-tenants REGISTRA as migrations dele em ``public.django_migrations`` mas só
cria ``auth_user`` no schema de cada cliente.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# Tabelas do app ``users`` do SynDoc (Client/Domain do django-tenants).
TABELAS_SYNDOC = ("users_client", "users_domain")


class Command(BaseCommand):
    help = "Cria o schema do painel (POSTGRES_SCHEMA) e aborta se o banco/schema for o do SynDoc."

    def handle(self, *args, **options):
        banco = connection.settings_dict.get("NAME")
        schema = getattr(settings, "POSTGRES_SCHEMA", "") or ""

        if schema and connection.vendor == "postgresql":
            self._preparar_schema(banco, schema)

        onde = f"schema '{schema}' do banco '{banco}'" if schema else f"banco '{banco}'"
        tabelas = set(connection.introspection.table_names())

        do_syndoc = sorted(t for t in TABELAS_SYNDOC if t in tabelas)
        if do_syndoc:
            raise CommandError(
                f"O {onde} é o do SynDoc (tem {', '.join(do_syndoc)}). NÃO apague o schema public: ele guarda "
                "o cadastro de todos os clientes. Use um schema próprio no mesmo banco "
                "(POSTGRES_SCHEMA=painel_assinaturas no .env) ou um banco exclusivo "
                "(`sudo -u postgres createdb --owner=ultradoc subscription_management`) e recrie o container."
            )

        if "django_migrations" in tabelas and "auth_user" not in tabelas:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM django_migrations WHERE app = %s LIMIT 1", ["auth"])
                if cursor.fetchone():
                    raise CommandError(
                        f"O {onde} registra as migrations do auth como aplicadas, mas a tabela auth_user "
                        "não existe: ele pertence a outro sistema (django-tenants). Use POSTGRES_SCHEMA "
                        "ou um banco exclusivo para o painel."
                    )

        self.stdout.write(self.style.SUCCESS(f"{onde[0].upper()}{onde[1:]} OK para o painel."))

    def _preparar_schema(self, banco, schema):
        with connection.cursor() as cursor:
            # Se o banco é o do SynDoc, o schema não pode ser o de um cliente.
            cursor.execute("SELECT to_regclass('public.users_client') IS NOT NULL")
            if cursor.fetchone()[0]:
                cursor.execute("SELECT 1 FROM public.users_client WHERE schema_name = %s", [schema])
                if cursor.fetchone():
                    raise CommandError(
                        f"POSTGRES_SCHEMA='{schema}' é o schema de um cliente do SynDoc. Escolha outro nome."
                    )
            cursor.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", [schema])
            if cursor.fetchone():
                return
            # Nome já validado nas settings (regex); aspas por garantia.
            cursor.execute(f'CREATE SCHEMA "{schema}"')
        self.stdout.write(f"Schema '{schema}' criado no banco '{banco}'.")
