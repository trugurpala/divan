# Canonical Windows fallback uninstaller for Codex.
param([string]$Manifest = "")
$ErrorActionPreference = "Stop"

$dst = if ($env:CODEX_SKILLS_DIR) {
  $env:CODEX_SKILLS_DIR
} else {
  Join-Path $env:USERPROFILE ".codex\skills"
}
$stateDir = if ($env:DIVAN_STATE_DIR) {
  $env:DIVAN_STATE_DIR
} else {
  Join-Path $env:USERPROFILE ".codex"
}

if (-not $Manifest) {
  $pointer = Join-Path $stateDir "divan-install-latest"
  if (Test-Path -LiteralPath $pointer -PathType Leaf) {
    $Manifest = (Get-Content -LiteralPath $pointer -Raw).Trim()
  } else {
    $latest = Get-ChildItem (Join-Path $stateDir "divan-install-*.tsv") -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTimeUtc | Select-Object -Last 1
    if (-not $latest) { throw "Divan kurulum kaydi bulunamadi: $stateDir" }
    $Manifest = $latest.FullName
  }
}
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
  throw "Kurulum kaydi bulunamadi: $Manifest"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python 3 bulunamadi; guvenli kaldirma calistirilamiyor." }
$helper = Join-Path $PSScriptRoot "legacy_state.py"
& $python.Source $helper migrate --manifest $Manifest --skills-dir $dst --state-dir $stateDir
if ($LASTEXITCODE -ne 0) { throw "Legacy Divan kaldirma islemi guvenli bicimde geri alindi." }
Write-Host "Divan karantinaya alindi; kullanilan kayit korundu -> $Manifest"
