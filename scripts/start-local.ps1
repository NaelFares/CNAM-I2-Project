param(
  [switch]$NoBuild
)

$composeArgs = @("up", "-d", "--remove-orphans")
if (-not $NoBuild) {
  $composeArgs += "--build"
}

docker compose @composeArgs
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$frontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }
$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }

Write-Host ""
Write-Host "Services demarres:" -ForegroundColor Green
Write-Host "- Frontend disponible a: http://localhost:$frontendPort"
Write-Host "- Backend API disponible a: http://localhost:$backendPort"
Write-Host "- Health backend disponible a: http://localhost:$backendPort/health"
Write-Host ""
Write-Host "Etat des conteneurs:" -ForegroundColor Cyan

docker compose ps
