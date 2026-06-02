param(
  [switch]$NoBuild,
  [switch]$NoLogs,
  [switch]$ForceCpu,
  [switch]$ForceGpu
)

function Invoke-ComposeUp {
  param(
    [string[]]$ComposeFiles
  )

  $args = @()
  $args += $ComposeFiles
  $args += @("up", "-d", "--remove-orphans")
  if (-not $NoBuild) {
    $args += "--build"
  }

  docker compose @args
}

$baseComposeFiles = @("-f", "docker-compose.yml")
$gpuComposeFiles = @("-f", "docker-compose.yml", "-f", "docker-compose.gpu.yml")
$activeComposeFiles = $baseComposeFiles
$gpuAttempted = $false
$accelerationMode = "CPU"

if ($ForceCpu -and $ForceGpu) {
  Write-Host "Options incompatibles: -ForceCpu et -ForceGpu." -ForegroundColor Red
  exit 2
}

if ($ForceGpu) {
  $gpuAttempted = $true
  $activeComposeFiles = $gpuComposeFiles
  Write-Host "Mode GPU demande: tentative de demarrage Ollama avec GPU." -ForegroundColor Cyan
  Invoke-ComposeUp -ComposeFiles $activeComposeFiles
  $exitCode = $LASTEXITCODE
  if ($exitCode -eq 0) {
    $accelerationMode = "GPU"
  } else {
    Write-Host "Demarrage GPU impossible. Relance automatique en CPU." -ForegroundColor Yellow
    $activeComposeFiles = $baseComposeFiles
    $accelerationMode = "CPU"
    Invoke-ComposeUp -ComposeFiles $activeComposeFiles
    $exitCode = $LASTEXITCODE
  }
} else {
  if ($ForceCpu) {
    Write-Host "Mode CPU force pour Ollama." -ForegroundColor Cyan
  } else {
    Write-Host "Mode CPU par defaut pour Ollama. Utilise -ForceGpu pour demander le GPU." -ForegroundColor Cyan
  }
  Invoke-ComposeUp -ComposeFiles $activeComposeFiles
  $exitCode = $LASTEXITCODE
}

if ($exitCode -ne 0) {
  exit $exitCode
}

$frontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }
$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }
$iaPort = if ($env:OLLAMA_PORT) { $env:OLLAMA_PORT } else { "11434" }

Write-Host ""
Write-Host "Services demarres:" -ForegroundColor Green
Write-Host "- Frontend disponible a: http://localhost:$frontendPort"
Write-Host "- Backend API disponible a: http://localhost:$backendPort"
Write-Host "- Health backend disponible a: http://localhost:$backendPort/health"
Write-Host "- IA service (Ollama) disponible a: http://localhost:$iaPort"
Write-Host "- Acceleration IA demandee: $accelerationMode"
if ($gpuAttempted -and $accelerationMode -eq "CPU") {
  Write-Host "  GPU detecte mais non utilisable par Docker Compose; fallback CPU applique." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Etat des conteneurs:" -ForegroundColor Cyan

docker compose @activeComposeFiles ps

if (-not $NoLogs) {
  Write-Host ""
  Write-Host "Logs en direct (Ctrl+C pour quitter les logs sans arreter les services)..." -ForegroundColor Yellow
  docker compose @activeComposeFiles logs -f --tail=100
}
