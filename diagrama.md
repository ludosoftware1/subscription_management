erDiagram
    Cidadao {
        int id PK
        string nome_completo
        string cpf "unique"
        date data_nascimento
        string situacao
        string cep
        string bairro
        string endereco
        string celular
        datetime data_cadastro
        int localidade_id FK "pode ser nulo"
    }

    Localidade {
        int id PK
        string nome "unique"
    }

    Beneficio {
        int id PK
        string nome
        string situacao
        int periodicidade_dias
    }

    BeneficioConcedido {
        UUID id PK
        datetime data_concessao
        int cidadao_id FK
        int beneficio_id FK
    }

    Configuracao {
        int id PK
        string nome_instituicao
        string pin_seguranca
    }

    Cidadao }o--|| Localidade : "possui"
    BeneficioConcedido ||--|{ Cidadao : "concedido para"
    BeneficioConcedido ||--|{ Beneficio : "é do tipo"

