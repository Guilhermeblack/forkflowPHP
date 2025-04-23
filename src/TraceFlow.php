<?php

namespace Bemagro\TraceFlow;

use Illuminate\Support\Facades\Http;
use InvalidArgumentException;

/**
 * TraceFlow - Cliente PHP para serviço de registro de logs GeoManager
 */
class TraceFlow
{
    // URL da API
    private string $url;
    
    // Cabeçalhos da requisição
    private array $headers;
    
    // Configurações padrão para todos os logs
    private int $platformId;
    private int $environmentId;
    private ?int $moduleId;
    private ?int $toolId;
    private ?int $scenarioId;
    private ?int $actionTagId;
    private ?int $processId;
    private ?int $proposalId;
    private ?int $userId;
    private ?int $customerId;
    private ?string $filename;
    private ?string $filenameLabel;
    private ?string $bucketUrl;
    private ?string $storage;
    private array $contentJson;
    private array $objects;

    /**
     * Construtor da classe TraceFlow
     * 
     * @param string $url URL da API de logs
     * @param array $headers Cabeçalhos HTTP (incluindo token de autenticação)
     * @param int $platformId ID da plataforma
     * @param int $environmentId ID do ambiente
     * @param int|null $moduleId ID do módulo (opcional)
     * @param int|null $toolId ID da ferramenta (opcional)
     * @param int|null $scenarioId ID do cenário (opcional)
     * @param int|null $actionTagId ID da ação (opcional)
     * @param int|null $processId ID do processo (opcional)
     * @param int|null $proposalId ID da proposta (opcional)
     * @param int|null $userId ID do usuário (opcional)
     * @param int|null $customerId ID do cliente (opcional)
     * @param string|null $filename Nome do arquivo (opcional)
     * @param string|null $filenameLabel Rótulo do arquivo (opcional)
     * @param string|null $bucketUrl URL do bucket (opcional)
     * @param string|null $storage Tipo de armazenamento (opcional)
     * @param array|null $contentJson Conteúdo JSON adicional (opcional)
     * @param array|null $objects Lista de objetos associados (opcional)
     * @throws InvalidArgumentException
     */
    public function __construct(
        string $url,
        array $headers,
        int $platformId,
        int $environmentId,
        ?int $moduleId = null,
        ?int $toolId = null,
        ?int $scenarioId = null,
        ?int $actionTagId = null,
        ?int $processId = null,
        ?int $proposalId = null,
        ?int $userId = null,
        ?int $customerId = null,
        ?string $filename = null,
        ?string $filenameLabel = null,
        ?string $bucketUrl = null,
        ?string $storage = null,
        ?array $contentJson = null,
        ?array $objects = null
    ) {
        if (empty($url)) {
            throw new InvalidArgumentException('URL não pode estar vazia');
        }
        if ($platformId <= 0) {
            throw new InvalidArgumentException('ID da plataforma deve ser um inteiro positivo');
        }
        if ($environmentId <= 0) {
            throw new InvalidArgumentException('ID do ambiente deve ser um inteiro positivo');
        }

        $this->url = rtrim($url, '/');
        $this->headers = $headers;
        $this->platformId = $platformId;
        $this->environmentId = $environmentId;
        $this->moduleId = $moduleId;
        $this->toolId = $toolId;
        $this->scenarioId = $scenarioId;
        $this->actionTagId = $actionTagId;
        $this->processId = $processId;
        $this->proposalId = $proposalId;
        $this->userId = $userId;
        $this->customerId = $customerId;
        $this->filename = $filename;
        $this->filenameLabel = $filenameLabel;
        $this->bucketUrl = $bucketUrl;
        $this->storage = $storage;
        $this->contentJson = $contentJson ?? [];
        $this->objects = $objects ?? [];
    }

    /**
     * Coleta métricas do sistema e hardware
     * 
     * @return array Dados de hardware e sistema
     */
    private function collectSystemMetrics(): array
    {
        $metrics = [];
        
        // CPU usage
        if (function_exists('sys_getloadavg')) {
            $load = sys_getloadavg();
            $cpuCores = 1;
            
            // Tenta obter o número de núcleos para calcular porcentagem corretamente
            if (PHP_OS_FAMILY === 'Linux') {
                $cores = shell_exec('nproc');
                if ($cores !== null && is_numeric(trim($cores))) {
                    $cpuCores = (int)trim($cores);
                }
            }
            
            $metrics['processador'] = round($load[0] * 100 / $cpuCores, 1);
        } else {
            $metrics['processador'] = 0;
        }
        
        // Memória
        if (PHP_OS_FAMILY === 'Linux') {
            $freeCommand = shell_exec('free -m');
            if ($freeCommand !== null) {
                $lines = explode("\n", $freeCommand);
                if (isset($lines[1])) {
                    $parts = preg_split('/\s+/', trim($lines[1]));
                    if (isset($parts[1]) && isset($parts[2])) {
                        $totalMem = (float)$parts[1];
                        $usedMem = (float)$parts[2];
                        $metrics['memoria'] = round($usedMem / 1024, 2) . "/" . round($totalMem / 1024, 2) . " GB";
                    } else {
                        $metrics['memoria'] = "N/A";
                    }
                } else {
                    $metrics['memoria'] = "N/A";
                }
            } else {
                $metrics['memoria'] = "N/A";
            }
        } else {
            $memoryTotal = function_exists('memory_get_usage') ? memory_get_usage(true) : 0;
            $metrics['memoria'] = round($memoryTotal / (1024 * 1024 * 1024), 2) . " GB";
        }
        
        // Disco
        $diskTotal = disk_total_space('/');
        $diskFree = disk_free_space('/');
        $diskUsed = $diskTotal - $diskFree;
        $metrics['disco'] = round($diskUsed / (1024 * 1024 * 1024), 2) . "/" . round($diskTotal / (1024 * 1024 * 1024), 2) . " GB";
        
        // IP Address
        $metrics['ip_address'] = $_SERVER['SERVER_ADDR'] ?? gethostbyname(gethostname());
        
        // MAC Address (requer privilégios em alguns sistemas)
        $macAddress = 'N/A';
        if (PHP_OS_FAMILY === 'Linux') {
            $ifconfigOutput = shell_exec("ifconfig 2>/dev/null || ip addr");
            if ($ifconfigOutput !== null) {
                preg_match('/ether (..:..:..:..:..:..)/i', $ifconfigOutput, $matches);
                if (!empty($matches[1])) {
                    $macAddress = $matches[1];
                } else {
                    // Alternativa para alguns sistemas Linux
                    preg_match('/link\/ether (..:..:..:..:..:..)/i', $ifconfigOutput, $matches);
                    if (!empty($matches[1])) {
                        $macAddress = $matches[1];
                    }
                }
            }
        }
        $metrics['mac_address'] = $macAddress;
        
        // Sistema Operacional
        $metrics['os_name'] = PHP_OS_FAMILY;
        
        // Versão do SO
        $osVersion = php_uname('r');
        $metrics['os_version'] = $osVersion;
        
        return $metrics;
    }

    /**
     * Cria um novo ponto de log na API
     * 
     * @param string $description Descrição do ponto
     * @param int|null $actionTagId ID da ação (sobrescreve o padrão)
     * @param int|null $environmentId ID do ambiente (sobrescreve o padrão)
     * @param int|null $moduleId ID do módulo (sobrescreve o padrão)
     * @param int|null $toolId ID da ferramenta (sobrescreve o padrão)
     * @param int|null $scenarioId ID do cenário (sobrescreve o padrão)
     * @param int|null $processId ID do processo (sobrescreve o padrão)
     * @param int|null $proposalId ID da proposta (sobrescreve o padrão)
     * @param int|null $userId ID do usuário (sobrescreve o padrão)
     * @param int|null $customerId ID do cliente (sobrescreve o padrão)
     * @param string|null $filename Nome do arquivo (sobrescreve o padrão)
     * @param string|null $filenameLabel Rótulo do arquivo (sobrescreve o padrão)
     * @param string|null $bucketUrl URL do bucket (sobrescreve o padrão)
     * @param string|null $storage Tipo de armazenamento (sobrescreve o padrão)
     * @param array|null $contentJson Conteúdo JSON adicional (sobrescreve o padrão)
     * @param array|null $objects Lista de objetos associados (sobrescreve o padrão)
     * @return array Resposta da API
     * @throws InvalidArgumentException
     */
    public function createPoint(
        string $description,
        ?int $actionTagId = null,
        ?int $environmentId = null,
        ?int $moduleId = null,
        ?int $toolId = null,
        ?int $scenarioId = null,
        ?int $processId = null,
        ?int $proposalId = null,
        ?int $userId = null,
        ?int $customerId = null,
        ?string $filename = null,
        ?string $filenameLabel = null,
        ?string $bucketUrl = null,
        ?string $storage = null,
        ?array $contentJson = null,
        ?array $objects = null
    ): array {
        if (empty($description)) {
            throw new InvalidArgumentException('Descrição não pode estar vazia');
        }

        // Adiciona dados do sistema ao contentJson
        $systemMetrics = $this->collectSystemMetrics();
        $finalContentJson = $contentJson ?? $this->contentJson;
        $finalContentJson['data_host'] = $systemMetrics;

        // Monta o payload com os dados padrão e sobrescreve com os dados específicos
        $payload = [
            'platform_id' => $this->platformId,
            'environment_id' => $environmentId ?? $this->environmentId,
            'description' => $description,
            'content_json' => $finalContentJson,
        ];

        // Adiciona os campos opcionais se definidos
        $optionalFields = [
            'module_id' => $moduleId ?? $this->moduleId,
            'tool_id' => $toolId ?? $this->toolId,
            'scenario_id' => $scenarioId ?? $this->scenarioId,
            'action_tag_id' => $actionTagId ?? $this->actionTagId,
            'process_id' => $processId ?? $this->processId,
            'proposal_id' => $proposalId ?? $this->proposalId,
            'user_id' => $userId ?? $this->userId,
            'customer_id' => $customerId ?? $this->customerId,
            'filename' => $filename ?? $this->filename,
            'filename_label' => $filenameLabel ?? $this->filenameLabel,
            'bucket_url' => $bucketUrl ?? $this->bucketUrl,
            'storage' => $storage ?? $this->storage,
            'objects' => $objects ?? $this->objects,
        ];

        foreach ($optionalFields as $key => $value) {
            if ($value !== null) {
                $payload[$key] = $value;
            }
        }

        // Envia a requisição para a API
        $response = Http::withHeaders($this->headers)->post($this->url, $payload);

        if ($response->failed()) {
            throw new \RuntimeException('Falha ao enviar log: ' . $response->body());
        }

        return $response->json();
    }
}