
# TraceflowPHP-lib

**Biblioteca PHP interna** da BemAgro para integração com serviços do **TraceFlow**. Esta biblioteca é utilizada exclusivamente em projetos internos.

> **Autor:** Guilherme Pereira  
> **Licença:** Proprietary  
> **Visibilidade:** Interna / Uso restrito à equipe da BemAgro

---

## 📦 Instalação via Composer (com servidor interno)

### 1. Adicione o repositório ao seu `composer.json`

A biblioteca está empacotada em um `.zip` e exposta via servidor HTTP. Adicione o seguinte bloco:

```json
"repositories": [
  {
    "type": "package",
    "package": {
      "name": "bemagro/traceflowphp",
      "version": "1.0.0",
      "dist": {
        "url": "http://10.0.2.3/packages/download/traceflowPHP-lib/traceflowPHP-lib.zip",
        "type": "zip"
      },
      "autoload": {
        "psr-4": {
          "Bemagro\\TraceFlow\\": "src/"
        }
      },
      "require": {
        "php": "^8.1",
        "illuminate/support": "^8.0",
        "illuminate/http": "^8.0"
      }
    }
  }
],
"require": {
  "bemagro/traceflowphp": "1.0.0"
}
```

> Certifique-se de que o link acima esteja acessível via navegador.

---

### 2. Permitir uso de HTTP (rede interna)

Como o Composer bloqueia HTTP por padrão, execute este comando antes:

```bash
composer config secure-http false
```

---

### 3. Instale a biblioteca

```bash
composer update bemagro/traceflowphp
```

---

## 🔧 Funcionalidades

A biblioteca `TraceflowPHP-lib` fornece integração direta com a API de logging do TraceFlow. Suas funcionalidades principais incluem:

- 📝 Criação de pontos de log customizados com nível de severidade e objetos relacionados.
- 📊 Coleta automática de métricas do ambiente (memória, CPU, IP, SO, etc.).
- 🔐 Envio autenticado de logs com cabeçalhos customizados.
- ✅ Pronta para uso com Laravel ou qualquer projeto PHP com suporte a `illuminate/http`.

Classe principal: `Bemagro\TraceFlow\TraceFlow`

---

## ✅ Exemplo de Uso

```php
require 'vendor/autoload.php';

use Bemagro\TraceFlow\TraceFlow;

$traceflow = new TraceFlow(
    url: 'https://logs.bemagro.com/api/logs',
    headers: [
        'Authorization' => 'Bearer seu-token-aqui',
        'Accept' => 'application/json',
        'Content-Type' => 'application/json'
    ],
    platform_id: 1,
    environment_id: 2,
    module_id: 3,
    content_json: [
        'usuario' => 'guilherme.pereira',
        'acao' => 'execucao de tarefa'
    ]
);

$response = $traceflow->createPoint(
    description: 'Início do processamento do otimizador',
    content_json: [
        'etapa' => 'pré-processamento',
        'parametros' => ['area_id' => 456, 'tipo' => 'pulverização']
    ],
    log_level: 'info',
    objects: [
        'entidade' => 'GFF',
        'referencia' => 'area_456'
    ]
);

print_r($response);
```

---

## 🛠️ Autoload e Namespace

A biblioteca segue o padrão **PSR-4**:

```json
"autoload": {
  "psr-4": {
    "Bemagro\\TraceFlow\\": "src/"
  }
}
```

A classe principal `TraceFlow` está localizada em `src/TraceFlow.php` com o seguinte namespace:

```php
namespace Bemagro\TraceFlow;
```

---

## 🧑‍💻 Autor

**Guilherme Pereira**  
Engenheiro de Software @ BemAgro

---

## 📃 Licença

Esta biblioteca é **proprietária**. Distribuição e uso externo são **proibidos**.  
Uso autorizado apenas em projetos internos da BemAgro.
