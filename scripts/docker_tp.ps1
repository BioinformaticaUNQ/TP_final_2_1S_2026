param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

# Wrapper de un solo comando para usar la CLI dentro de Docker.
# Construye la imagen la primera vez (si no existe) y despues solo la reutiliza.
# Los JSON generados en /app/output quedan en .\output del host.
#
# Uso:
#   .\scripts\docker_tp.ps1 --help
#   .\scripts\docker_tp.ps1 articles/solo_agrotoxicos/acute_toxicity_atrazine.pdf --skip-blast --output-dir output/docker_pdf
#   .\scripts\docker_tp.ps1 articles/proteina_y_agro --skip-blast --output-dir output/docker_dir
#   .\scripts\docker_tp.ps1 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output/docker_doi

$ErrorActionPreference = 'Stop'

$Image = 'tp-bioinfo:latest'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

if (-not (docker images -q $Image)) {
    Write-Host "Imagen '$Image' no encontrada. Construyendo (solo la primera vez)..." -ForegroundColor Cyan
    docker build -t $Image $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Fallo el build de la imagen Docker." }
}

$OutputDir = Join-Path $RepoRoot 'output'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

docker run --rm -v "${OutputDir}:/app/output" $Image @Rest
