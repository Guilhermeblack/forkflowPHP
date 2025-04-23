<?php

namespace Bemagro\TraceFlow\Tests;

use Bemagro\TraceFlow\TraceFlow;
use PHPUnit\Framework\TestCase;
use Illuminate\Support\Facades\Http;

class TraceFlowTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Http::fake([
            '*' => Http::response(['message' => 'Log enfileirado com sucesso!', 'log_id' => 123], 200)
        ]);
    }

    public function testConstructorValidatesParameters()
    {
        $this->expectException(\InvalidArgumentException::class);
        new TraceFlow('', ['Authorization' => 'Bearer token'], 1, 1);
    }

    public function testConstructorValidatesPlatformId()
    {
        $this->expectException(\InvalidArgumentException::class);
        new TraceFlow('http://example.com', ['Authorization' => 'Bearer token'], 0, 1);
    }

    public function testConstructorValidatesEnvironmentId()
    {
        $this->expectException(\InvalidArgumentException::class);
        new TraceFlow('http://example.com', ['Authorization' => 'Bearer token'], 1, 0);
    }

    public function testCreatePointBasic()
    {
        $traceFlow = new TraceFlow(
            'http://example.com/api/v1/logs',
            ['Authorization' => 'Bearer test-token'],
            1, // platformId
            2  // environmentId
        );

        $response = $traceFlow->createPoint('Teste de log');
        
        $this->assertEquals(['message' => 'Log enfileirado com sucesso!', 'log_id' => 123], $response);
        
        Http::assertSent(function ($request) {
            return $request->url() == 'http://example.com/api/v1/logs' &&
                   $request->hasHeader('Authorization', 'Bearer test-token') &&
                   $request['platform_id'] == 1 &&
                   $request['environment_id'] == 2 &&
                   $request['description'] == 'Teste de log' &&
                   isset($request['content_json']['data_host']);
        });
    }

    public function testCreatePointWithAllParameters()
    {
        $traceFlow = new TraceFlow(
            'http://example.com/api/v1/logs',
            ['Authorization' => 'Bearer test-token'],
            1, // platformId
            2, // environmentId
            3, // moduleId
            4, // toolId
            5, // scenarioId
            6, // actionTagId
            7, // processId
            8, // proposalId
            9, // userId
            10, // customerId
            'test.txt', // filename
            'Test File', // filenameLabel
            'bucket/test.txt', // bucketUrl
            'aws', // storage
            ['origem' => 'teste unitário'], // contentJson
            [['storage' => 'aws', 'url' => 'shapes/teste.geojson', 'description' => 'Arquivo teste']] // objects
        );

        $response = $traceFlow->createPoint('Teste de log completo');
        
        $this->assertEquals(['message' => 'Log enfileirado com sucesso!', 'log_id' => 123], $response);
        
        Http::assertSent(function ($request) {
            return $request->url() == 'http://example.com/api/v1/logs' &&
                   $request['platform_id'] == 1 &&
                   $request['environment_id'] == 2 &&
                   $request['module_id'] == 3 &&
                   $request['tool_id'] == 4 &&
                   $request['scenario_id'] == 5 &&
                   $request['action_tag_id'] == 6 &&
                   $request['process_id'] == 7 &&
                   $request['proposal_id'] == 8 &&
                   $request['user_id'] == 9 &&
                   $request['customer_id'] == 10 &&
                   $request['filename'] == 'test.txt' &&
                   $request['filename_label'] == 'Test File' &&
                   $request['bucket_url'] == 'bucket/test.txt' &&
                   $request['storage'] == 'aws' &&
                   $request['content_json']['origem'] == 'teste unitário' &&
                   isset($request['content_json']['data_host']) &&
                   count($request['objects']) == 1 &&
                   $request['objects'][0]['storage'] == 'aws';
        });
    }

    public function testCreatePointWithOverrides()
    {
        $traceFlow = new TraceFlow(
            'http://example.com/api/v1/logs',
            ['Authorization' => 'Bearer test-token'],
            1, // platformId
            2, // environmentId
            3  // moduleId
        );

        $response = $traceFlow->createPoint(
            'Teste com sobrescrita',
            101, // actionTagId
            4,   // environmentId (sobrescreve o padrão)
            null, // moduleId (usa o padrão)
            null, // toolId
            null, // scenarioId
            null, // processId
            null, // proposalId
            null, // userId
            null, // customerId
            'outro.txt', // filename
            null, // filenameLabel
            null, // bucketUrl
            null, // storage
            ['teste' => 'sobrescrita'], // contentJson
            [['storage' => 'oracle', 'url' => 'shapes/outro.geojson', 'description' => 'Outro arquivo']] // objects
        );
        
        $this->assertEquals(['message' => 'Log enfileirado com sucesso!', 'log_id' => 123], $response);
        
        Http::assertSent(function ($request) {
            return $request->url() == 'http://example.com/api/v1/logs' &&
                   $request['platform_id'] == 1 &&
                   $request['environment_id'] == 4 && // Sobrescrito
                   $request['module_id'] == 3 &&      // Valor padrão
                   $request['action_tag_id'] == 101 && // Sobrescrito
                   $request['filename'] == 'outro.txt' && // Sobrescrito
                   $request['content_json']['teste'] == 'sobrescrita' && // Conteúdo específico
                   isset($request['content_json']['data_host']) && // Métricas do sistema incluídas
                   $request['objects'][0]['storage'] == 'oracle'; // Objetos sobrescritos
        });
    }
}