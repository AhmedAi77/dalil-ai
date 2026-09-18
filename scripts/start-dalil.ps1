[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelName = "qwen3:8b"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Refresh-ToolPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Install-WithWinget([string]$Id, [string]$Name) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "$Name is missing and winget is unavailable. Install $Name manually, then run this command again."
    }
    Write-Step "Installing $Name"
    & $winget.Source install --id $Id -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "$Name installation failed (exit code $LASTEXITCODE)." }
    Refresh-ToolPath
}

function Wait-Until([scriptblock]$Check, [int]$Seconds, [string]$FailureMessage) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        try { if (& $Check) { return } } catch { }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)
    throw $FailureMessage
}

Set-Location $projectRoot

Write-Step "Checking Docker Desktop"
$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if (-not $docker) {
    Install-WithWinget "Docker.DockerDesktop" "Docker Desktop"
    $docker = Get-Command docker.exe -ErrorAction SilentlyContinue
    if (-not $docker) {
        $dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
        if (Test-Path $dockerPath) { $env:Path = "$(Split-Path $dockerPath);$env:Path" }
    }
}

$dockerReady = Test-Path "\\.\pipe\docker_engine"
if (-not $dockerReady) {
    $desktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $desktop)) {
        throw "Docker Desktop was installed but could not be found. Restart Windows, then run this command again."
    }
    Write-Step "Starting Docker Desktop"
    Start-Process -FilePath $desktop
    Wait-Until { Test-Path "\\.\pipe\docker_engine" } 180 "Docker did not become ready. Finish Docker Desktop's first-run setup or restart Windows, then try again."
}
$nativePreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
docker info *> $null
$dockerExitCode = $LASTEXITCODE
$ErrorActionPreference = $nativePreference
if ($dockerExitCode -ne 0) { throw "Docker Desktop is open, but its engine is unavailable." }

Write-Step "Checking Ollama"
$ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
if (-not $ollama) {
    Install-WithWinget "Ollama.Ollama" "Ollama"
    $ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if (-not $ollama) {
        $ollamaPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
        if (Test-Path $ollamaPath) { $env:Path = "$(Split-Path $ollamaPath);$env:Path" }
    }
}
if (-not (Get-Command ollama.exe -ErrorAction SilentlyContinue)) {
    throw "Ollama was installed but is not available yet. Restart Windows, then run this command again."
}

# Docker reaches the Windows Ollama service through host.docker.internal.
$env:OLLAMA_HOST = "0.0.0.0:11434"
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", $env:OLLAMA_HOST, "User")
Write-Step "Starting Ollama with Docker access"
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Start-Process -FilePath (Get-Command ollama.exe).Source -ArgumentList "serve" -WindowStyle Hidden
Wait-Until {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null
    $true
} 60 "Ollama did not start on port 11434."

Write-Step "Checking local AI model $modelName"
$ErrorActionPreference = "SilentlyContinue"
$installedModels = (& ollama list 2>$null | Out-String)
$ErrorActionPreference = $nativePreference
if ($installedModels -notmatch [regex]::Escape($modelName)) {
    $ErrorActionPreference = "Continue"
    & ollama pull $modelName
    $ollamaExitCode = $LASTEXITCODE
    $ErrorActionPreference = $nativePreference
    if ($ollamaExitCode -ne 0) { throw "Could not download Ollama model $modelName." }
}

Write-Step "Checking application configuration"
$envFile = Join-Path $projectRoot ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $projectRoot ".env.example") $envFile
    Write-Host "Created .env from .env.example." -ForegroundColor Yellow
}
$envText = Get-Content $envFile -Raw
if ($envText -notmatch '(?m)^PINECONE_API_KEY=\S+') {
    $key = Read-Host "Paste your Pinecone API key"
    if ([string]::IsNullOrWhiteSpace($key)) { throw "A Pinecone API key is required." }
    $envText = $envText -replace '(?m)^PINECONE_API_KEY=.*$', "PINECONE_API_KEY=$key"
    Set-Content -LiteralPath $envFile -Value $envText -Encoding utf8
}

Write-Step "Stopping old Dalil AI services and clearing ports 3000/8000"
$ErrorActionPreference = "SilentlyContinue"
docker compose down --remove-orphans 2>$null
$ErrorActionPreference = $nativePreference
foreach ($port in 3000, 8000) {
    $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($listener in $listeners) {
        if ($listener.OwningProcess -gt 0) {
            $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Stopping $($process.ProcessName) on port $port (PID $($process.Id))." -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force
            }
        }
    }
}

Write-Step "Building and starting Dalil AI"
$ErrorActionPreference = "Continue"
docker compose up -d --build
$composeExitCode = $LASTEXITCODE
$ErrorActionPreference = $nativePreference
if ($composeExitCode -ne 0) { throw "Docker Compose could not start Dalil AI." }

Write-Step "Waiting for health checks"
Wait-Until {
    $containerId = cmd.exe /d /c "docker compose ps -q backend 2>nul"
    if (-not $containerId) { return $false }
    $health = cmd.exe /d /c "docker inspect --format={{.State.Health.Status}} $containerId 2>nul"
    $health -eq "healthy"
} 180 "The backend did not become healthy. Run 'docker compose logs backend' for details."
$ErrorActionPreference = "SilentlyContinue"
docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://host.docker.internal:11434/api/tags', timeout=10)"
$ollamaDockerExitCode = $LASTEXITCODE
$ErrorActionPreference = $nativePreference
if ($ollamaDockerExitCode -ne 0) {
    throw "The backend container cannot reach Ollama. Restart Windows and run the same command again."
}
Wait-Until {
    $response = Invoke-WebRequest -UseBasicParsing "http://localhost:3000" -TimeoutSec 5
    $response.StatusCode -eq 200
} 90 "The frontend did not become available. Run 'docker compose logs frontend' for details."

Write-Host "`nDalil AI is ready: http://localhost:3000" -ForegroundColor Green
Start-Process "http://localhost:3000"
