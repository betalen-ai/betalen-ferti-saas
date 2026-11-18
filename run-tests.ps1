$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from beta_billing_tests
$code = $LASTEXITCODE
docker compose -f docker-compose.test.yml down -v
exit $code