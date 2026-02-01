import random
from datetime import date, timedelta, datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from faker import Faker

# Removed imports for removed apps
# from apps.estrutura_organizacional.models import Secretaria, Condutor, LocadorPrestadorServico, PostoCombustivel
# from apps.veiculos.models import Veiculo, ModeloVeiculo, Maquina
# from apps.abastecimento.models import Abastecimento
# from apps.manutencao.models import Manutencao, Peca, Servico, TipoManutencao, StatusOS

class Command(BaseCommand):
    help = 'Populate the database with comprehensive realistic data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando processo de seeding abrangente...'))
        fake = Faker('pt_BR')

        # --- Limpeza ---
        self.stdout.write('🧹 Limpando dados antigos...')
        Manutencao.objects.all().delete()
        Peca.objects.all().delete()
        Servico.objects.all().delete()
        Abastecimento.objects.all().delete()
        Veiculo.objects.all().delete()
        ModeloVeiculo.objects.all().delete()
        Maquina.objects.all().delete()
        Condutor.objects.all().delete()
        Secretaria.objects.all().delete()
        LocadorPrestadorServico.objects.all().delete()
        PostoCombustivel.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Group.objects.all().delete()

        # --- Grupos e Usuários ---
        admin_group, created = Group.objects.get_or_create(name='administrador')
        if created: self.stdout.write('👤 Grupo "administrador" criado.')

        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            admin_user.groups.add(admin_group)
            self.stdout.write('👑 Usuário administrador criado.')

        self.stdout.write('🏗️ Criando estrutura organizacional completa...')

        # --- Secretarias Municipais (5 secretarias essenciais) ---
        secretarias_data = [
            {'nome': 'Secretaria Municipal de Saúde', 'sigla': 'SMS'},
            {'nome': 'Secretaria Municipal de Educação', 'sigla': 'SME'},
            {'nome': 'Secretaria Municipal de Obras', 'sigla': 'SMO'},
            {'nome': 'Secretaria Municipal de Administração', 'sigla': 'SMA'},
            {'nome': 'Secretaria Municipal de Transporte', 'sigla': 'SMT'}
        ]

        secretarias = []
        for data in secretarias_data:
            secretaria = Secretaria.objects.create(**data)
            secretarias.append(secretaria)
        self.stdout.write(f'🏛️ {len(secretarias)} secretarias municipais criadas.')

        # --- Condutores (5 condutores essenciais) ---
        categorias_cnh = ['B', 'C', 'D', 'E']
        condutores = []

        for i in range(5):
            categoria = random.choice(categorias_cnh)
            condutor = Condutor.objects.create(
                nome_completo=fake.name(),
                cpf=fake.cpf(),
                cnh=fake.bothify(text='###########'),
                categoria_cnh=categoria,
                data_validade_cnh=date.today() + timedelta(days=random.randint(365, 365*3)),
                secretaria=random.choice(secretarias),
                telefone=fake.phone_number(),
                email=fake.email(),
            )
            condutores.append(condutor)
        self.stdout.write(f'👥 {len(condutores)} condutores criados.')

        # --- Empresas Locadoras/Prestadoras (2 empresas) ---
        tipos_servico = [
            'Locação de Veículos Leves',
            'Locação de Máquinas e Equipamentos'
        ]

        locadores = []
        for i in range(2):
            locador = LocadorPrestadorServico.objects.create(
                nome_fantasia=fake.company(),
                razao_social=fake.company_suffix(),
                cnpj=fake.cnpj(),
                endereco=fake.address(),
                cep=fake.postcode(),
                bairro=fake.neighborhood(),
                cidade='São Paulo',
                estado='SP',
                telefone=fake.phone_number(),
                email=fake.email(),
                tipo_servico=random.choice(tipos_servico)
            )
            locadores.append(locador)
        self.stdout.write(f'🏢 {len(locadores)} empresas locadoras/prestadoras criadas.')

        # --- Postos de Combustível (3 postos credenciados) ---
        postos = []
        bandeiras = ['Petrobras', 'Shell', 'Ipiranga']

        for i in range(3):
            bandeira = random.choice(bandeiras)
            nome_posto = f'Posto {bandeira} {fake.neighborhood()}'

            posto = PostoCombustivel.objects.create(
                nome=nome_posto,
                cnpj=fake.cnpj(),
                endereco=fake.address(),
                cep=fake.postcode(),
                bairro=fake.neighborhood(),
                cidade='São Paulo',
                estado='SP',
                telefone=fake.phone_number(),
                email=fake.email(),
                credenciado=True,
                status=True,
                data_credenciamento=date.today() - timedelta(days=random.randint(30, 365)),
                observacoes=f'Posto {bandeira} credenciado para abastecimento da frota municipal'
            )
            postos.append(posto)
        self.stdout.write(f'⛽ {len(postos)} postos de combustível criados.')

        # --- Modelos de Veículos (50 modelos realistas) ---
        modelos_data = [
            # Carros de passeio
            {'descricao_marca': 'Fiat', 'descricao_modelo': 'Mobi', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Fiat', 'descricao_modelo': 'Uno', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Fiat', 'descricao_modelo': 'Palio', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Chevrolet', 'descricao_modelo': 'Onix', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Chevrolet', 'descricao_modelo': 'Prisma', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Chevrolet', 'descricao_modelo': 'Cruze', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Volkswagen', 'descricao_modelo': 'Gol', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Volkswagen', 'descricao_modelo': 'Polo', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Volkswagen', 'descricao_modelo': 'Virtus', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Toyota', 'descricao_modelo': 'Corolla', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Toyota', 'descricao_modelo': 'Etios', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Honda', 'descricao_modelo': 'Civic', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Honda', 'descricao_modelo': 'Fit', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Hyundai', 'descricao_modelo': 'HB20', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Hyundai', 'descricao_modelo': 'Creta', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Renault', 'descricao_modelo': 'Kwid', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Renault', 'descricao_modelo': 'Sandero', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Nissan', 'descricao_modelo': 'Versa', 'tipo_veiculo': 'carro'},
            {'descricao_marca': 'Nissan', 'descricao_modelo': 'Kicks', 'tipo_veiculo': 'carro'},

            # Motocicletas
            {'descricao_marca': 'Honda', 'descricao_modelo': 'NXR 160 Bros', 'tipo_veiculo': 'moto'},
            {'descricao_marca': 'Honda', 'descricao_modelo': 'CG 160', 'tipo_veiculo': 'moto'},
            {'descricao_marca': 'Honda', 'descricao_modelo': 'Biz 125', 'tipo_veiculo': 'moto'},
            {'descricao_marca': 'Yamaha', 'descricao_modelo': 'Factor 150', 'tipo_veiculo': 'moto'},
            {'descricao_marca': 'Yamaha', 'descricao_modelo': 'YBR 125', 'tipo_veiculo': 'moto'},

            # Caminhões e Vans
            {'descricao_marca': 'Mercedes-Benz', 'descricao_modelo': 'Actros', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Mercedes-Benz', 'descricao_modelo': 'Atego', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Volkswagen', 'descricao_modelo': 'Constellation', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Scania', 'descricao_modelo': 'R450', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Volvo', 'descricao_modelo': 'FH 460', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Iveco', 'descricao_modelo': 'Tector', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Ford', 'descricao_modelo': 'Cargo 816', 'tipo_veiculo': 'caminhao'},
            {'descricao_marca': 'Fiat', 'descricao_modelo': 'Ducato', 'tipo_veiculo': 'van'},
            {'descricao_marca': 'Mercedes-Benz', 'descricao_modelo': 'Sprinter', 'tipo_veiculo': 'van'},
            {'descricao_marca': 'Volkswagen', 'descricao_modelo': 'Crafter', 'tipo_veiculo': 'van'},
            {'descricao_marca': 'Iveco', 'descricao_modelo': 'Daily', 'tipo_veiculo': 'van'},

            # Ônibus
            {'descricao_marca': 'Mercedes-Benz', 'descricao_modelo': 'OF-1721', 'tipo_veiculo': 'onibus'},
            {'descricao_marca': 'Volvo', 'descricao_modelo': 'B270F', 'tipo_veiculo': 'onibus'},
            {'descricao_marca': 'Scania', 'descricao_modelo': 'K310', 'tipo_veiculo': 'onibus'},
            {'descricao_marca': 'Agrale', 'descricao_modelo': 'MA 9.2', 'tipo_veiculo': 'onibus'},
            {'descricao_marca': 'Marcopolo', 'descricao_modelo': 'Paradiso G7', 'tipo_veiculo': 'onibus'},
        ]

        modelos_veiculo = []
        for i, data in enumerate(modelos_data):
            modelo = ModeloVeiculo.objects.create(
                numero_modelo=f'MOD-{i+1:03d}',
                codigo_marca=i+1,
                **data
            )
            modelos_veiculo.append(modelo)
        self.stdout.write(f'🚗 {len(modelos_veiculo)} modelos de veículo criados.')

        # --- Veículos (50 veículos realistas) ---
        cores = ['branco', 'prata', 'preto', 'cinza', 'vermelho', 'azul', 'verde', 'amarelo']
        situacoes = [1, 1, 1, 1, 1, 1, 1, 2, 3]  # 78% em uso, 11% em manutenção, 11% baixados
        tipos_frota = [1, 1, 1, 1, 1, 1, 1, 2, 3]  # 78% próprios, 11% locados, 11% prestação

        veiculos_criados = []
        for i in range(50):
            modelo = random.choice(modelos_veiculo)
            ano_fab = random.randint(2015, 2024)
            ano_mod = max(ano_fab, random.randint(2015, 2024))

            # Calcular quilometragem baseada no tempo de uso
            anos_uso = date.today().year - ano_fab
            km_base = anos_uso * random.randint(15000, 30000)  # 15-30k km por ano
            quilometragem = km_base + random.randint(-5000, 5000)  # Variação

            # Capacidade do tanque baseada no tipo de veículo
            if modelo.tipo_veiculo == 'moto':
                capacidade_tanque = random.randint(13, 18)
                capacidade_passageiros = 2
            elif modelo.tipo_veiculo in ['caminhao', 'onibus']:
                capacidade_tanque = random.randint(200, 500)
                capacidade_passageiros = random.randint(2, 45)
            elif modelo.tipo_veiculo == 'van':
                capacidade_tanque = random.randint(60, 100)
                capacidade_passageiros = random.randint(8, 15)
            else:  # carro
                capacidade_tanque = random.randint(40, 60)
                capacidade_passageiros = random.randint(4, 5)

            # Tipo de combustível baseado no modelo
            if modelo.tipo_veiculo in ['caminhao', 'onibus', 'van']:
                tipo_combustivel = 2  # Diesel
            elif modelo.tipo_veiculo == 'moto':
                tipo_combustivel = 1  # Gasolina
            else:
                tipo_combustivel = random.choice([1, 5, 5, 5])  # 25% gasolina, 75% flex

            situacao = random.choice(situacoes)
            tipo_frota = random.choice(tipos_frota)

            # Proprietário para veículos locados/cessão
            empresa_locadora = None
            cpf_cnpj_proprietario = fake.cpf()  # Sempre fornecer um valor
            if tipo_frota in [2, 3]:  # Locado ou Cessão
                empresa_locadora = random.choice(locadores)
                cpf_cnpj_proprietario = empresa_locadora.cnpj

            veiculo = Veiculo.objects.create(
                placa=fake.license_plate().replace('-', ''),
                modelo_veiculo=modelo,
                ano_fabricacao=ano_fab,
                ano_modelo=ano_mod,
                cor=random.choice(cores),
                numero_chassi=fake.bothify(text='?BWZ?????????????').upper(),
                renavam=fake.bothify(text='###########'),
                secretaria=random.choice(secretarias),
                situacao=situacao,
                tipo_frota=tipo_frota,
                empresa_locadora=empresa_locadora,
                cpf_cnpj_proprietario=cpf_cnpj_proprietario,
                tipo_combustivel=tipo_combustivel,
                data_aquisicao=date.today() - timedelta(days=random.randint(30, 365*9)),  # Até 9 anos
                quilometragem_inicial=0,
                quilometragem_atual=max(0, quilometragem),
                capacidade_tanque_litros=capacidade_tanque,
                capacidade_passageiros=capacidade_passageiros,
                observacoes=fake.sentence(nb_words=6)
            )
            veiculos_criados.append(veiculo)

        self.stdout.write(f'🚗 {len(veiculos_criados)} veículos criados.')

        # --- Máquinas (20 máquinas realistas) ---
        tipos_maquinas = [
            {'tipo': 'Retroescavadeira', 'modelos': ['580N', '590M'], 'potencias': ['97 HP', '110 HP'], 'consumo': [8.5, 9.2]},
            {'tipo': 'Escavadeira Hidráulica', 'modelos': ['320D', '336D'], 'potencias': ['110 HP', '125 HP'], 'consumo': [9.8, 11.2]},
            {'tipo': 'Pá Carregadeira', 'modelos': ['950H', '962H'], 'potencias': ['165 HP', '185 HP'], 'consumo': [14.2, 16.1]},
            {'tipo': 'Caminhão Basculante', 'modelos': ['730C', '735C'], 'potencias': ['205 HP', '225 HP'], 'consumo': [18.5, 20.2]},
        ]

        maquinas_criadas = []
        for i in range(20):
            tipo_maquina = random.choice(tipos_maquinas)
            modelo_idx = random.randint(0, len(tipo_maquina['modelos']) - 1)

            ano_fab = random.randint(2015, 2024)
            anos_uso = date.today().year - ano_fab
            horas_base = anos_uso * random.randint(800, 1500)  # 800-1500 horas por ano
            horimetro = horas_base + random.randint(-200, 200)

            situacao = random.choice([1, 1, 1, 1, 1, 1, 1, 2, 3])  # 78% em uso, 11% manutenção, 11% baixadas
            tipo_frota = random.choice([1, 1, 1, 1, 1, 1, 1, 2, 3])  # 78% próprios, 11% locados, 11% prestação

            empresa_locadora = None
            cpf_cnpj_proprietario = fake.cpf()  # Sempre fornecer um valor
            if tipo_frota in [2, 3]:
                empresa_locadora = random.choice(locadores)
                cpf_cnpj_proprietario = empresa_locadora.cnpj

            maquina = Maquina.objects.create(
                codigo_maquina=f'{tipo_maquina["tipo"][:3].upper()}-{i+1:03d}',
                descricao=tipo_maquina['tipo'],
                ano_fabricacao=ano_fab,
                codigo_situacao=situacao,
                codigo_tipo_maquina=tipo_frota,
                empresa_locadora=empresa_locadora,
                cpf_cnpj_proprietario=cpf_cnpj_proprietario,
                data_aquisicao=date.today() - timedelta(days=random.randint(30, 365*9)),
                modelo=tipo_maquina['modelos'][modelo_idx],
                potencia=tipo_maquina['potencias'][modelo_idx],
                consumo_hora_maquina=Decimal(str(tipo_maquina['consumo'][modelo_idx])),
                tipo_combustivel='diesel',
                secretaria=random.choice(secretarias),
                horimetro_atual=max(0, horimetro),
                observacoes=fake.sentence(nb_words=5)
            )
            maquinas_criadas.append(maquina)

        self.stdout.write(f'🏗️ {len(maquinas_criadas)} máquinas criadas.')

        # --- Abastecimentos (1 por veículo/máquina com quilometragem progressiva) ---
        veiculos_criados = list(Veiculo.objects.all())
        maquinas_criadas = list(Maquina.objects.all())

        abastecimentos_criados = []
        for item in veiculos_criados + maquinas_criadas:
            tipo_item = 'veiculo' if isinstance(item, Veiculo) else 'maquina'
            categoria = 1 if tipo_item == 'veiculo' else 2

            # Data recente
            data_abastecimento = date.today() - timedelta(days=random.randint(1, 30))

            # Condutor aleatório
            condutor = random.choice(condutores)

            # Posto aleatório
            posto = random.choice(postos)

            # Tipo de combustível baseado no item
            if tipo_item == 'maquina':
                tipo_combustivel = 'diesel'
                litros = round(random.uniform(50, 150), 1)
                valor_litro = Decimal('5.50')
            else:
                if item.tipo_combustivel == 1:  # Gasolina
                    tipo_combustivel = 'gasolina'
                    litros = round(random.uniform(30, 60), 1)
                    valor_litro = Decimal('6.50')
                elif item.tipo_combustivel == 2:  # Diesel
                    tipo_combustivel = 'diesel'
                    litros = round(random.uniform(40, 80), 1)
                    valor_litro = Decimal('5.20')
                else:  # Flex
                    tipo_combustivel = 'gasolina'
                    litros = round(random.uniform(35, 65), 1)
                    valor_litro = Decimal('6.50')

            # Quilometragem/horas progressivas
            if tipo_item == 'veiculo':
                # Quilometragem anterior baseada na quilometragem atual do veículo
                quilometragem_anterior = max(0, item.quilometragem_atual - random.randint(100, 500))
                quilometragem_atual = item.quilometragem_atual
                horas_utilizadas = None
            else:
                horas_utilizadas = round(random.uniform(4, 12), 1)
                quilometragem_atual = None
                quilometragem_anterior = None

            abastecimento = Abastecimento.objects.create(
                veiculo_ou_maquina_id=item.pk,
                veiculo_ou_maquina_tipo=tipo_item,
                categoria_frota=categoria,
                condutor=condutor,
                data_abastecimento=data_abastecimento,
                quilometragem_anterior=quilometragem_anterior,
                quilometragem_atual=quilometragem_atual,
                horas_utilizadas=horas_utilizadas,
                tipo_combustivel=tipo_combustivel,
                litros=Decimal(str(litros)),
                valor_litro=valor_litro,
                posto_combustivel=posto,
                nota_fiscal=f'NF{len(abastecimentos_criados)+1:06d}',
                cupom_fiscal=f'CUP{len(abastecimentos_criados)+1:06d}',
                observacoes=fake.sentence(nb_words=4)
            )
            abastecimentos_criados.append(abastecimento)

        self.stdout.write(f'⛽ {len(abastecimentos_criados)} abastecimentos criados.')

        # --- Manutenções (20 manutenções básicas) ---
        tipos_manutencao = ['CORRETIVA', 'PREVENTIVA']
        status_os = ['ABERTA', 'EM_ANDAMENTO', 'FINALIZADA', 'CANCELADA']

        manutencoes_criadas = []
        for i in range(200):
            # Escolher veículo ou máquina (60% veículos, 40% máquinas)
            if random.random() < 0.6:
                item = random.choice(veiculos_criados)
                tipo_item = 'veiculo'
            else:
                item = random.choice(maquinas_criadas)
                tipo_item = 'maquina'

            # Data aleatória nos últimos 2 anos
            dias_atras = random.randint(1, 730)
            data_abertura = date.today() - timedelta(days=dias_atras)

            # Status baseado na data
            if dias_atras > 180:
                status = random.choice(['FINALIZADA', 'FINALIZADA', 'CANCELADA'])
            elif dias_atras > 30:
                status = random.choice(['FINALIZADA', 'EM_ANDAMENTO', 'ABERTA'])
            else:
                status = random.choice(['ABERTA', 'EM_ANDAMENTO'])

            # Tipo de manutenção
            tipo_manutencao = random.choice(tipos_manutencao)

            # Descrição baseada no tipo
            descricoes = {
                'CORRETIVA': ['Reparo de falha no motor', 'Troca de peça quebrada', 'Reparo elétrico', 'Conserto de vazamento'],
                'PREVENTIVA': ['Revisão programada', 'Troca preventiva', 'Inspeção de segurança', 'Manutenção preventiva']
            }
            descricao = random.choice(descricoes[tipo_manutencao])

            # Quilometragem/horimetro na manutenção
            if tipo_item == 'veiculo':
                km_manutencao = item.quilometragem_atual - (dias_atras * random.randint(20, 100))
                km_manutencao = max(0, km_manutencao)
                horimetro_manutencao = None
            else:
                horas_manutencao = item.horimetro_atual - (dias_atras * random.uniform(1, 5))
                horimetro_manutencao = max(0, horas_manutencao)
                km_manutencao = None

            # Datas
            data_fechamento = None
            if status == 'FINALIZADA':
                dias_duracao = random.randint(1, 30)
                data_fechamento = data_abertura + timedelta(days=dias_duracao)

            manutencao = Manutencao.objects.create(
                veiculo=item if tipo_item == 'veiculo' else None,
                maquina=item if tipo_item == 'maquina' else None,
                tipo_manutencao=tipo_manutencao,
                status_os=status,
                data_inicio=data_abertura if status in ['EM_ANDAMENTO', 'FINALIZADA'] else None,
                data_final=data_fechamento if status == 'FINALIZADA' else None,
                quilometragem=km_manutencao,
                descricao_servico=f'{descricao} - {fake.sentence(nb_words=8)}',
                observacoes=fake.sentence(nb_words=6) if random.random() < 0.7 else None
            )

            # Adicionar peças e serviços para manutenções finalizadas
            if status == 'FINALIZADA':
                # Adicionar 1-3 peças
                num_pecas = random.randint(1, 3)
                pecas_nomes = [
                    'Óleo de Motor 15W40', 'Filtro de Óleo', 'Filtro de Ar', 'Filtro de Combustível',
                    'Velas de Ignição', 'Bateria 60Ah', 'Palhetas Limpador', 'Pastilhas de Freio',
                    'Discos de Freio', 'Amortecedores', 'Correia de Acessórios', 'Bomba de Água'
                ]

                for j in range(num_pecas):
                    nome_peca = random.choice(pecas_nomes)
                    quantidade = random.randint(1, 4)
                    valor_unitario = round(random.uniform(10, 500), 2)

                    Peca.objects.create(
                        manutencao=manutencao,
                        nome_peca=nome_peca,
                        quantidade=Decimal(str(quantidade)),
                        valor_unitario=Decimal(str(valor_unitario))
                    )

                # Adicionar 1-2 serviços
                num_servicos = random.randint(1, 2)
                servicos_descricoes = [
                    'Troca de Óleo e Filtros', 'Revisão Completa', 'Alinhamento e Balanceamento',
                    'Troca de Velas', 'Troca de Bateria', 'Troca de Palhetas', 'Troca de Pastilhas de Freio',
                    'Diagnóstico Eletrônico', 'Lavagem Completa', 'Reparo de Suspensão'
                ]

                for j in range(num_servicos):
                    descricao_servico = random.choice(servicos_descricoes)
                    valor_servico = round(random.uniform(50, 300), 2)

                    Servico.objects.create(
                        manutencao=manutencao,
                        descricao=descricao_servico,
                        valor=Decimal(str(valor_servico))
                    )

            manutencoes_criadas.append(manutencao)

        self.stdout.write(f'🔧 {len(manutencoes_criadas)} manutenções criadas.')

        self.stdout.write(self.style.SUCCESS('🎉 Processo de seeding abrangente concluído com sucesso!'))
        self.stdout.write(self.style.SUCCESS('📊 Resumo dos dados criados:'))
        self.stdout.write(f'   • {len(secretarias)} Secretarias Municipais')
        self.stdout.write(f'   • {len(condutores)} Condutores')
        self.stdout.write(f'   • {len(locadores)} Empresas Locadoras/Prestadoras')
        self.stdout.write(f'   • {len(postos)} Postos de Combustível')
        self.stdout.write(f'   • {len(modelos_veiculo)} Modelos de Veículos')
        self.stdout.write(f'   • {len(veiculos_criados)} Veículos')
        self.stdout.write(f'   • {len(maquinas_criadas)} Máquinas')
        self.stdout.write(f'   • {len(abastecimentos_criados)} Abastecimentos Históricos')
        self.stdout.write(f'   • {len(manutencoes_criadas)} Manutenções')
