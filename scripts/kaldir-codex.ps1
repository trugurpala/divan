# Divan Codex kurulum kaydini kullanarak yalniz kayitli hedefleri kaldirir.
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

$dstFull = [IO.Path]::GetFullPath($dst).TrimEnd([IO.Path]::DirectorySeparatorChar)
$prefix = $dstFull + [IO.Path]::DirectorySeparatorChar
$rows = Import-Csv -LiteralPath $Manifest -Delimiter "`t"
foreach ($row in $rows) {
  $target = [IO.Path]::GetFullPath($row.hedef)
  if (-not $target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Kayitli hedef skill dizini disinda: $target"
  }
  if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
  }
  if ($row.yedek -and (Test-Path -LiteralPath $row.yedek)) {
    Move-Item -LiteralPath $row.yedek -Destination $target
    Write-Host "  geri yuklendi: $($row.skill)"
  } else {
    Write-Host "  kaldirildi: $($row.skill)"
  }
}

Write-Host "Divan kaldirildi; kullanilan kayit korundu -> $Manifest"
