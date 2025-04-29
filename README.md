
Serviço dedicado para registro de logs no ecossistema, facilitando o monitoramento de eventos, operações e erros de forma estruturada.

🚀 Funcionalidade Principal
Este módulo está focado exclusivamente em:

Registro de eventos do sistema e de usuários

Armazenamento seguro e escalável dos logs

Consulta por múltiplos filtros: tipo, origem, usuário, timestamp etc.

📂 Estrutura do Projeto
graphql
Copiar
Editar
-logger/
│
├── app/
│   ├── main.py           # Ponto de entrada FastAPI
│   ├── models/           # Modelos do banco de dados
│   ├── routes/           # Endpoints REST para registro e consulta
│   ├── services/         # Lógica de negócio (gravação e leitura de logs)
│   └── utils/            # Ferramentas auxiliares
│
├── alembic/              # Controle de versão do banco de dados
├── Dockerfile
├── docker-compose.yml
└── README.md
📥 Endpoints Disponíveis
POST /log
Registra um novo log no sistema.

Payload esperado:

json
Copiar
Editar
{
  "level": "info",
  "message": "Operação iniciada com sucesso",
  "source": "optimizer",
  "user": "admin",
  "extra": {
    "operation_id": "12345"
  }
}
