TraceFlow PHP
Biblioteca PHP para criação de logs centralizados no sistema GeoManager, inspirado na biblioteca TraceFlow em Python.

Instalação
Você pode instalar esta biblioteca via Composer:

bash
composer require bemagro/traceflow
Requisitos
PHP 7.4 ou superior
Illuminate/Http (componente do Laravel)
Uso Básico
php
use Bemagro\TraceFlow\TraceFlow;

// Inicialize o cliente TraceFlow com configurações padrão
$trace = new TraceFlow(
    url: "http://localhost:8000/api/v1/logs/", 
    headers: ["Authorization" => "Bearer seu-token"],
    platformId: 1,
    environmentId: 4
);

// Crie um ponto de log
$response = $trace->createPoint(
    description: "Upload de arquivo finalizado",
    actionTagId: 101,
    filename: "linha.geojson",
    bucketUrl: "bucket/123/linha.geojson",
    storage: "oracle",
    objects: [
        [
            "storage" => "oracle",
            "url" => "shapes/entrada.geojson",
            "description" => "Arquivo original"
        ],
        [
            "storage" => "aws",
            "url" => "shapes/saida.geojson",
            "description" => "Resultado"
        ]
    ]
);

print_r($response);
Uso Avançado
Configuração com todos os parâmetros disponíveis
php
$trace = new TraceFlow(
    url: "http://localhost:8000/api/v1/logs/",
    headers: ["Authorization" => "Bearer seu-token"],
    platformId: 1,          // ID da plataforma (obrigatório)
    environmentId: 4,       // ID do ambiente (obrigatório)
    moduleId: 3,            // ID do módulo (opcional)
    toolId: 5,              // ID da ferramenta (opcional)
    scenarioId: 2,          // ID do cenário (opcional)
    actionTagId: 101,       // ID da ação (opcional)
    processId: 42,          // ID do processo (opcional)
    proposalId: 123,        // ID da proposta (opcional)
    userId: 789,            // ID do usuário (opcional)
    customerId: 456,        // ID do cliente (opcional)
    filename: "exemplo.geojson", // Nome do arquivo (opcional)
    filenameLabel: "Arquivo de exemplo", // Rótulo do arquivo (opcional)
    bucketUrl: "bucket/exemplo.geojson", // URL do bucket (opcional)
    storage: "oracle",      // Tipo de armazenamento (opcional)
    contentJson: [          // Conteúdo JSON adicional (opcional)
        "origem" => "validador de geometria",
        "versao" => "1.0.0"
    ],
    objects: [              // Lista de objetos associados (opcional)
        [
            "storage" => "oracle",
            "url" => "shapes/entrada.geojson",
            "description" => "Arquivo original"
        ]
    ]
);
Monitoramento de Hardware e Sistema
Por padrão, todos os logs incluem métricas de hardware e sistema no campo content_json["data_host"]. Exemplo de log gerado:

json
{
  "description": "Upload de arquivo finalizado",
  "content_json": {
    "origem": "validador de geometria",
    "data_host": {
      "processador": 45.5,
      "memoria": "8.23/16.00 GB",
      "disco": "120.45/500.00 GB",
      "ip_address": "10.0.2.3",
      "mac_address": "00:50:56:c0:00:08",
      "os_name": "Linux",
      "os_version": "5.15.0-73-generic"
    }
  },
  // ...outros campos
}
Parâmetros da Classe TraceFlow
Estes são valores padrão, usados em todos os logs, mas que podem ser sobrescritos ao chamar createPoint():

Parâmetro	Tipo	Obrigatório	Descrição
url	string	Sim	URL da API
headers	array	Sim	Cabeçalhos com token
platformId	int	Sim	ID da plataforma
environmentId	int	Sim	ID do ambiente
moduleId	int	Não	ID do módulo
toolId	int	Não	ID da ferramenta
scenarioId	int	Não	ID do cenário
actionTagId	int	Não	ID da ação executada
processId	int	Não	ID do processo
proposalId	int	Não	ID da proposta
userId	int	Não	ID do usuário
customerId	int	Não	ID do cliente
filename	string	Não	Nome do arquivo
filenameLabel	string	Não	Rótulo do arquivo
bucketUrl	string	Não	Caminho do bucket
storage	string	Não	Tipo de storage (aws, oracle)
contentJson	array	Não	Dados extras em JSON
objects	array	Não	Lista de objetos associados
Formato do parâmetro objects
php
$objects = [
    [
        "storage" => "oracle",
        "url" => "shapes/entrada.geojson",
        "description" => "Arquivo original"
    ],
    [
        "storage" => "aws",
        "url" => "shapes/saida.geojson",
        "description" => "Arquivo processado"
    ]
]
Resposta da API
json
{
  "message": "Log enfileirado com sucesso!",
  "log_id": 123,
  "log_level": "info",
  "objects": [...]
}
Exemplo de Teste Rápido
php
$trace = new TraceFlow(
    url: "http://localhost:8000/api/v1/logs/", 
    headers: ["Authorization" => "Bearer token"],
    platformId: 1,
    environmentId: 2
);

$response = $trace->createPoint(
    description: "Log de teste rápido",
    objects: [
        [
            "storage" => "aws",
            "url" => "shapes/teste.geojson",
            "description" => "Arquivo teste"
        ]
    ]
);
Contribuindo
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

Licença
Este projeto está licenciado sob a licença MIT.

