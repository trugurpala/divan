# Divan'i Codex icin kurar (Windows PowerShell).
# DIVAN_REF ile bir tag/commit, CODEX_SKILLS_DIR ile hedef sabitlenebilir.
$ErrorActionPreference = "Stop"

$ref = if ($env:DIVAN_REF) { $env:DIVAN_REF } else { "main" }
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
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$work = Join-Path ([IO.Path]::GetTempPath()) ("divan-kur-" + [Guid]::NewGuid())

try {
  New-Item -ItemType Directory -Force -Path $work | Out-Null
  if ($env:DIVAN_SOURCE_DIR) {
    $source = $env:DIVAN_SOURCE_DIR
  } else {
    $zip = Join-Path $work "divan.zip"
    $expanded = Join-Path $work "expanded"
    Invoke-WebRequest "https://github.com/trugurpala/divan/archive/$ref.zip" -OutFile $zip
    Expand-Archive $zip -DestinationPath $expanded
    $source = (Get-ChildItem $expanded -Directory | Select-Object -First 1).FullName
  }

  if (-not (Test-Path (Join-Path $source "plugins"))) {
    throw "Divan kaynagi bulunamadi: $source"
  }

  New-Item -ItemType Directory -Force -Path $dst, $stateDir | Out-Null
  $backupRoot = Join-Path $stateDir "divan-backups\$stamp"
  $manifest = Join-Path $stateDir "divan-install-$stamp.tsv"
  "skill`thedef`tyedek" | Set-Content -Encoding utf8 $manifest
  $seen = @{}

  $skills = Get-ChildItem (Join-Path $source "plugins\*\skills\*") -Directory
  if (-not $skills) { throw "Kurulacak skill bulunamadi." }

  foreach ($skill in $skills) {
    if (-not (Test-Path (Join-Path $skill.FullName "SKILL.md"))) { continue }
    $name = $skill.Name
    if ($seen.ContainsKey($name)) { throw "Tekrarlanan skill adi: $name" }
    $seen[$name] = $true

    $target = Join-Path $dst $name
    $backup = ""
    if (Test-Path $target) {
      New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
      $backup = Join-Path $backupRoot $name
      Move-Item $target $backup
    }

    try {
      Copy-Item $skill.FullName -Destination $target -Recurse
    } catch {
      if ($backup -and (Test-Path $backup)) { Move-Item $backup $target }
      throw "$name kopyalanamadi; onceki surum geri getirildi. $($_.Exception.Message)"
    }
    "$name`t$target`t$backup" | Add-Content -Encoding utf8 $manifest
    Write-Host "  vezir: $name"
  }

  Write-Host ""
  Write-Host "Divan kuruldu -> $dst"
  Write-Host "Kurulum kaydi -> $manifest"
  Write-Host "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
} finally {
  if (Test-Path $work) { Remove-Item $work -Recurse -Force }
}
