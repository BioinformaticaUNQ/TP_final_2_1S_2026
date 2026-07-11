$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BlastDir = Join-Path $RepoRoot "data\blast"
$DbDir = Join-Path $RepoRoot "data\db"
$FastaDir = Join-Path $RepoRoot "data\fasta"
$BlastBin = Join-Path $BlastDir "ncbi-blast-2.17.0+\bin"
$Blastp = Join-Path $BlastBin "blastp.exe"
$MakeBlastDb = Join-Path $BlastBin "makeblastdb.exe"
$HumanFasta = Join-Path $FastaDir "human_proteome_up000005640.fasta"
$HumanDb = Join-Path $DbDir "human_proteome"

New-Item -ItemType Directory -Force -Path $BlastDir, $DbDir, $FastaDir | Out-Null

if (-not (Test-Path $Blastp)) {
    $BlastUrl = "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.17.0+-x64-win64.tar.gz"
    $BlastTar = Join-Path $BlastDir "ncbi-blast-2.17.0+-x64-win64.tar.gz"
    Write-Host "Descargando BLAST+ (137 MB)..."
    Invoke-WebRequest -Uri $BlastUrl -OutFile $BlastTar -UseBasicParsing
    Write-Host "Extrayendo BLAST+..."
    tar -xzf $BlastTar -C $BlastDir
    Remove-Item $BlastTar -ErrorAction SilentlyContinue
}

if (-not (Test-Path $HumanFasta)) {
    $UniProtUrl = "https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=fasta&query=(proteome:UP000005640)%20AND%20(reviewed:true)"
    $HumanGz = "$HumanFasta.gz"
    Write-Host "Descargando proteoma humano de UniProt..."
    Invoke-WebRequest -Uri $UniProtUrl -OutFile $HumanGz -UseBasicParsing
    $in = [System.IO.File]::OpenRead($HumanGz)
    $gzip = New-Object System.IO.Compression.GzipStream($in, [System.IO.Compression.CompressionMode]::Decompress)
    $out = [System.IO.File]::Create($HumanFasta)
    $gzip.CopyTo($out)
    $out.Close(); $gzip.Close(); $in.Close()
    Remove-Item $HumanGz
}

if (-not (Test-Path "$HumanDb.phr")) {
    Write-Host "Creando base de datos BLAST local..."
    & $MakeBlastDb -in $HumanFasta -dbtype prot -out $HumanDb -parse_seqids -title "Homo sapiens reference proteome (UniProt UP000005640)"
}

$env:PATH = "$BlastBin;$env:PATH"
$env:BLAST_MODE = "local"
$env:BLASTP_BIN = $Blastp
$env:HUMAN_PROTEOME_DB = $HumanDb

Write-Host ""
Write-Host "BLAST local listo."
& $Blastp -version
Write-Host ""
Write-Host "Variables de esta sesion: BLASTP_BIN, HUMAN_PROTEOME_DB, BLAST_MODE=local"
Write-Host "Probar en esta misma consola:"
Write-Host "  tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local"