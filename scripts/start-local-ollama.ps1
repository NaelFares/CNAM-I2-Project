param(
  [switch]$NoBuild,
  [switch]$NoLogs
)

$resetSeedAnswer = Read-Host "Reinitialiser les donnees de test (seed) au demarrage ? [o/N]"
if ($resetSeedAnswer -match '^(o|oui|y|yes)$') {
  $env:RESET_SEED = "1"
  Write-Host "Les donnees de test seront regenerees au demarrage du backend." -ForegroundColor Cyan
} else {
  $env:RESET_SEED = "0"
}

$composeArgs = @("-f", "docker/docker-compose.ollama.yml")
$upArgs = @($composeArgs)
$upArgs += @("up", "-d", "--remove-orphans")
if (-not $NoBuild) {
  $upArgs += "--build"
}

Write-Host "Mode IA : Ollama local CPU" -ForegroundColor Cyan
Write-Host "Ollama  : actif, image et modele telecharges au premier lancement" -ForegroundColor Yellow

docker compose @upArgs
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$frontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }
$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }
$iaPort = if ($env:OLLAMA_PORT) { $env:OLLAMA_PORT } else { "11434" }

Write-Host ""
Write-Host "Frontend : http://localhost:$frontendPort"
Write-Host "Backend  : http://localhost:$backendPort"
Write-Host "Health   : http://localhost:$backendPort/health"
Write-Host "Ollama   : http://localhost:$iaPort"
docker compose @composeArgs ps

if (-not $NoLogs) {
  Write-Host ""
  Write-Host "Logs en direct (Ctrl+C quitte les logs sans arreter les services)..." -ForegroundColor Yellow
  docker compose @composeArgs logs -f --tail=100
}
