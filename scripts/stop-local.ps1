$composeArgs = @("-f", "docker/docker-compose.ollama.yml")

docker compose @composeArgs down --remove-orphans
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Services arretes (frontend, backend, database et Ollama s'il etait actif)." -ForegroundColor Yellow
Write-Host ""
Write-Host "Etat des conteneurs:" -ForegroundColor Cyan

docker compose @composeArgs ps
