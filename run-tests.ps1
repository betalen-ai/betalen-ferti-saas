$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$code = 0
foreach ($testService in @(
    "beta_billing_tests",
    "beta_organization_tests",
    "beta_inventory_tests",
    "beta_email_tests"
)) {
    docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from $testService
    if ($LASTEXITCODE -ne 0) {
        $code = $LASTEXITCODE
        break
    }
}
docker compose -f docker-compose.test.yml down -v
exit $code