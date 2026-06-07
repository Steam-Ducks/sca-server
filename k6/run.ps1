# Uso:
#   .\k6\run.ps1              -> roda todos os cenarios em sequencia
#   .\k6\run.ps1 smoke        -> roda apenas o smoke
#   .\k6\run.ps1 smoke load   -> roda smoke e load

param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Scenarios
)

$serverDir = Split-Path $PSScriptRoot
$envFile = Join-Path $serverDir '.env'

if (-not (Test-Path $envFile)) {
    Write-Error "Arquivo .env nao encontrado em $serverDir"
    exit 1
}

$envArgs = Get-Content $envFile |
    Where-Object { $_ -match '^K6_' } |
    ForEach-Object {
        $k, $v = $_ -split '=', 2
        "--env", "$k=$($v.Trim())"
    }

if ($envArgs.Count -eq 0) {
    Write-Error "Nenhuma variavel K6_* encontrada no .env"
    exit 1
}

# Extrair BASE_URL do .env ou usar padrao
$baseUrl = (Get-Content $envFile | Where-Object { $_ -match '^K6_BASE_URL=' } |
    Select-Object -First 1) -replace '^K6_BASE_URL=', ''
if (-not $baseUrl) { $baseUrl = 'http://localhost:8000' }

$healthUrl = "$baseUrl/api/health/"

function Test-Server {
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        return $r.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

if (-not (Test-DockerRunning)) {
    Write-Host "Docker Desktop nao esta aberto. Iniciando..." -ForegroundColor Yellow
    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerExe)) {
        Write-Error "Docker Desktop nao encontrado em '$dockerExe'. Abra manualmente e tente novamente."
        exit 1
    }
    Start-Process $dockerExe

    Write-Host "Aguardando Docker Desktop inicializar..." -ForegroundColor Yellow
    $timeout = 120
    $elapsed = 0
    while (-not (Test-DockerRunning)) {
        if ($elapsed -ge $timeout) {
            Write-Error "Docker Desktop nao inicializou em $timeout segundos."
            exit 1
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
        Write-Host "  ...aguardando Docker ($elapsed s)" -ForegroundColor DarkGray
    }
    Write-Host "Docker Desktop pronto.`n" -ForegroundColor Green
}

if (-not (Test-Server)) {
    Write-Host "Subindo containers..." -ForegroundColor Yellow
    Push-Location $serverDir
    docker compose up -d
    Pop-Location

    Write-Host "Aguardando servidor ficar disponivel..." -ForegroundColor Yellow
    $timeout = 120
    $elapsed = 0
    while (-not (Test-Server)) {
        if ($elapsed -ge $timeout) {
            Write-Error "Servidor nao respondeu em $timeout segundos. Verifique: docker compose logs"
            exit 1
        }
        Start-Sleep -Seconds 3
        $elapsed += 3
        Write-Host "  ...aguardando servidor ($elapsed s)" -ForegroundColor DarkGray
    }
    Write-Host "Servidor disponivel.`n" -ForegroundColor Green
} else {
    Write-Host "Servidor ja esta rodando.`n" -ForegroundColor Green
}

$allScenarios = @('smoke', 'load', 'stress', 'soak', 'escalation')

$toRun = if ($Scenarios.Count -gt 0) { $Scenarios } else { $allScenarios }

$scenariosDir = Join-Path $PSScriptRoot 'scenarios'
$failed = @()

$env:K6_PROMETHEUS_RW_TREND_STATS = "p(50),p(95),p(99),max"
$env:K6_PROMETHEUS_RW_TREND_AS_NATIVE_HISTOGRAM = "false"

# Credenciais Grafana Cloud (lidas do .env)
$rwUrl  = (Get-Content $envFile | Where-Object { $_ -match '^GF_CLOUD_METRICS_URL=' }  | Select-Object -First 1) -replace '^GF_CLOUD_METRICS_URL=', ''
$rwUser = (Get-Content $envFile | Where-Object { $_ -match '^GF_CLOUD_METRICS_USER=' } | Select-Object -First 1) -replace '^GF_CLOUD_METRICS_USER=', ''
$rwPass = (Get-Content $envFile | Where-Object { $_ -match '^GF_CLOUD_METRICS_API_KEY=' } | Select-Object -First 1) -replace '^GF_CLOUD_METRICS_API_KEY=', ''

if ($rwUrl -and $rwUser -and $rwPass) {
    $env:K6_PROMETHEUS_RW_SERVER_URL = $rwUrl
    $env:K6_PROMETHEUS_RW_USERNAME   = $rwUser
    $env:K6_PROMETHEUS_RW_PASSWORD   = $rwPass
    Write-Host "Metricas enviadas para Grafana Cloud." -ForegroundColor DarkGray
} else {
    $env:K6_PROMETHEUS_RW_SERVER_URL = "http://localhost:9090/api/v1/write"
    Write-Host "Credenciais Grafana Cloud nao encontradas - usando Prometheus local." -ForegroundColor Yellow
}

foreach ($name in $toRun) {
    $file = Join-Path $scenariosDir "$name.js"

    if (-not (Test-Path $file)) {
        Write-Warning "Cenario nao encontrado: $name (pulando)"
        continue
    }

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " Rodando: $name" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    k6 run @envArgs `
      --out experimental-prometheus-rw `
      $file

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Cenario '$name' terminou com falha (exit $LASTEXITCODE)"
        $failed += $name
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($failed.Count -eq 0) {
    Write-Host " Todos os cenarios passaram." -ForegroundColor Green
} else {
    Write-Host " Cenarios com falha: $($failed -join ', ')" -ForegroundColor Red
    exit 1
}
