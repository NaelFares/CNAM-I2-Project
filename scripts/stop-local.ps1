docker compose down --remove-orphans
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Services arretes." -ForegroundColor Yellow
Write-Host ""
Write-Host "Etat des conteneurs:" -ForegroundColor Cyan

docker compose ps
