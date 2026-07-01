$ErrorActionPreference = 'Stop'

$VenvPath = Join-Path $PSScriptRoot '..\.venv_test'
$Python = Join-Path $VenvPath 'Scripts\python.exe'
$Cli = Join-Path $VenvPath 'Scripts\tp-bioinfo.exe'

if (-not (Test-Path $Python)) {
    python -m venv $VenvPath
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[test]"
& $Python -m pytest -q
& $Cli '10.1042/bj3180001'
