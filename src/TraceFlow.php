<?php

namespace Bemagro\TraceFlow;

use Illuminate\Support\Facades\Http;
use InvalidArgumentException;

class TraceFlow
{
    protected $url;
    protected $headers;
    protected $platformId;
    protected $environmentId;
    protected $moduleId;
    protected $contentJson;

    public function __construct(
        string $url,
        array $headers,
        int $platform_id,
        int $environment_id,
        int $module_id,
        array $content_json = []
    ) {
        $this->url = $url;
        $this->headers = $headers;
        $this->platformId = $platform_id;
        $this->environmentId = $environment_id;
        $this->moduleId = $module_id;
        $this->contentJson = $content_json;
    }

    public function createPoint(
        string $description,
        array $content_json = [],
        string $log_level = 'info',
        array $objects = []
    ): array {
        if (empty($description)) {
            throw new InvalidArgumentException('Descrição não pode estar vazia');
        }

        // Coleta métricas do sistema
        $systemMetrics = $this->collectSystemMetrics();

        // Combina content_json fornecido com métricas do sistema
        $finalContentJson = array_merge($this->contentJson, $content_json);
        $finalContentJson['data_host'] = $systemMetrics;

        // Monta o payload para a API
        $payload = [
            'platform_id' => $this->platformId,
            'environment_id' => $this->environmentId,
            'module_id' => $this->moduleId,
            'description' => $description,
            'log_level' => $log_level,
            'content_json' => $finalContentJson,
            'objects' => $objects,
        ];

        // Envia a requisição para a API
        $response = Http::withHeaders($this->headers)->post($this->url, $payload);

        if ($response->failed()) {
            throw new \RuntimeException('Falha ao enviar log: ' . $response->body());
        }

        return $response->json();
    }

    protected function collectSystemMetrics(): array
    {
        // Coleta de métricas existentes
        $metrics = [
            'memory_usage' => memory_get_usage(),
            'peak_memory_usage' => memory_get_peak_usage(),
            'execution_time' => microtime(true) - LARAVEL_START,
            'server' => [
                'php_version' => phpversion(),
                'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'unknown',
                'host' => gethostname(),
            ],
        ];

        // Coleta de informações adicionais solicitadas
        $metrics['processador'] = $this->getProcessorUsage();
        $metrics['memoria'] = $this->getMemoryInfo();
        $metrics['disco'] = $this->getDiskInfo();
        $metrics['ip_address'] = $this->getIpAddress();
        $metrics['mac_address'] = $this->getMacAddress();
        $metrics['os_name'] = $this->getOsName();
        $metrics['os_version'] = $this->getOsVersion();
        $metrics['kernel_version'] = $this->getKernelVersion();

        return $metrics;
    }

    protected function getProcessorUsage(): float
    {
        // No Linux, podemos usar /proc/stat para calcular a utilização da CPU
        if (file_exists('/proc/stat')) {
            $stat1 = file_get_contents('/proc/stat');
            sleep(1); // Aguarda 1 segundo para calcular a diferença
            $stat2 = file_get_contents('/proc/stat');

            $cpu1 = $this->parseCpuStats($stat1);
            $cpu2 = $this->parseCpuStats($stat2);

            $diffIdle = $cpu2['idle'] - $cpu1['idle'];
            $diffTotal = array_sum($cpu2) - array_sum($cpu1);
            $usage = $diffTotal ? (1 - $diffIdle / $diffTotal) * 100 : 0;

            return round($usage, 2);
        }

        return 0; // Valor padrão caso não seja possível calcular
    }

    protected function parseCpuStats(string $stat): array
    {
        $lines = explode("\n", $stat);
        $cpuLine = array_filter($lines, fn($line) => strpos($line, 'cpu ') === 0);
        $cpuLine = reset($cpuLine);
        $stats = preg_split('/\s+/', trim($cpuLine));
        array_shift($stats); // Remove 'cpu'
        return [
            'user' => (int)$stats[0],
            'nice' => (int)$stats[1],
            'system' => (int)$stats[2],
            'idle' => (int)$stats[3],
            'iowait' => (int)$stats[4],
            'irq' => (int)$stats[5],
            'softirq' => (int)$stats[6],
        ];
    }

    protected function getMemoryInfo(): string
    {
        if (file_exists('/proc/meminfo')) {
            $meminfo = file_get_contents('/proc/meminfo');
            preg_match('/MemTotal:\s+(\d+)/', $meminfo, $total);
            preg_match('/MemFree:\s+(\d+)/', $meminfo, $free);
            $totalGb = isset($total[1]) ? round($total[1] / 1024 / 1024, 2) : 0;
            $usedGb = isset($total[1], $free[1]) ? round(($total[1] - $free[1]) / 1024 / 1024, 2) : 0;
            return "$usedGb/$totalGb GB";
        }
        return "0/0 GB"; // Valor padrão
    }

    protected function getDiskInfo(): string
    {
        $path = '/'; // Raiz do sistema de arquivos
        $free = disk_free_space($path);
        $total = disk_total_space($path);
        $used = $total - $free;
        $usedGb = round($used / 1024 / 1024 / 1024, 2);
        $totalGb = round($total / 1024 / 1024 / 1024, 2);
        return "$usedGb/$totalGb GB";
    }

    protected function getIpAddress(): string
    {
        if (function_exists('shell_exec')) {
            $ip = shell_exec("ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -n1");
            return trim($ip) ?: 'unknown';
        }
        return $_SERVER['SERVER_ADDR'] ?? 'unknown';
    }

    protected function getMacAddress(): string
    {
        if (function_exists('shell_exec')) {
            $mac = shell_exec("ip link show | grep ether | awk '{print $2}' | head -n1");
            return trim($mac) ?: 'unknown';
        }
        return 'unknown';
    }

    protected function getOsName(): string
    {
        return php_uname('s') ?: 'unknown';
    }

    protected function getOsVersion(): string
    {
        if (file_exists('/etc/os-release')) {
            $osRelease = parse_ini_file('/etc/os-release');
            return $osRelease['VERSION_ID'] ?? 'unknown';
        }
        return php_uname('r') ?: 'unknown';
    }

    protected function getKernelVersion(): string
    {
        return php_uname('r') ?: 'unknown';
    }
}