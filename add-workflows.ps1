<#
.SYNOPSIS  Adds GitHub Actions CI/CD workflows to betalen-ferti-saas.
.USAGE     cd C:\Users\PC\betalen-ai\betalen-ferti-saas ; .\add-workflows.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function New-File($path, $content) {
    $full = Join-Path (Get-Location).Path $path
    $dir = Split-Path -Parent $full
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $text = ($content -replace "`r`n", "`n")
    [System.IO.File]::WriteAllText($full, $text, (New-Object System.Text.UTF8Encoding($false)))
}

# ---------- CI: test + build on every push / PR ----------
New-File ".github/workflows/ci.yml" @'
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    name: Test ${{ matrix.service }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        service:
          - api-gateway
          - beta_organization
          - beta_billing
          - beta_inventory
          - beta_reports
    defaults:
      run:
        working-directory: services/${{ matrix.service }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: services/${{ matrix.service }}/requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/betalen_test
        run: pytest tests/ -v --cov=app --cov-report=term-missing

  docker-build:
    name: Build ${{ matrix.name }}
    runs-on: ubuntu-latest
    needs: test
    strategy:
      fail-fast: false
      matrix:
        include:
          - { name: api-gateway,       context: services/api-gateway }
          - { name: beta_organization, context: services/beta_organization }
          - { name: beta_billing,      context: services/beta_billing }
          - { name: beta_inventory,    context: services/beta_inventory }
          - { name: beta_reports,      context: services/beta_reports }
          - { name: shop-pos-angular,  context: frontends/shop-pos-angular }
          - { name: backoffice-react,  context: frontends/backoffice-react }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build image (no push)
        uses: docker/build-push-action@v6
        with:
          context: ${{ matrix.context }}
          push: false
          cache-from: type=gha,scope=${{ matrix.name }}
          cache-to: type=gha,mode=max,scope=${{ matrix.name }}

  compose-validate:
    name: Validate compose files
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cp .env.example .env
      - run: docker compose -f docker-compose.yml config -q
      - run: docker compose -f docker-compose.test.yml config -q
'@

# ---------- Publish images to GitHub Container Registry ----------
New-File ".github/workflows/docker-publish.yml" @'
name: Publish images

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io

jobs:
  publish:
    name: Publish ${{ matrix.name }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        include:
          - { name: api-gateway,       context: services/api-gateway }
          - { name: beta_organization, context: services/beta_organization }
          - { name: beta_billing,      context: services/beta_billing }
          - { name: beta_inventory,    context: services/beta_inventory }
          - { name: beta_reports,      context: services/beta_reports }
          - { name: shop-pos-angular,  context: frontends/shop-pos-angular }
          - { name: backoffice-react,  context: frontends/backoffice-react }
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Image metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.name }}
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=sha
            type=semver,pattern={{version}}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ${{ matrix.context }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=${{ matrix.name }}
          cache-to: type=gha,mode=max,scope=${{ matrix.name }}
'@

# ---------- Dependabot: keep dependencies and actions updated ----------
New-File ".github/dependabot.yml" @'
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly

  - package-ecosystem: pip
    directory: "/services/api-gateway"
    schedule:
      interval: weekly
  - package-ecosystem: pip
    directory: "/services/beta_organization"
    schedule:
      interval: weekly
  - package-ecosystem: pip
    directory: "/services/beta_billing"
    schedule:
      interval: weekly
  - package-ecosystem: pip
    directory: "/services/beta_inventory"
    schedule:
      interval: weekly
  - package-ecosystem: pip
    directory: "/services/beta_reports"
    schedule:
      interval: weekly
'@

Write-Host "Workflows created in .github/" -ForegroundColor Green
Write-Host "Next: git add .github ; git commit -m 'ci: add workflows' ; git push" -ForegroundColor Cyan