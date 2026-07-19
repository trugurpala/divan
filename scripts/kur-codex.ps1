# Divan'i Codex icin kurar (Windows PowerShell).
# DIVAN_REF ile bir tag/commit, CODEX_SKILLS_DIR ile hedef sabitlenebilir.
$ErrorActionPreference = "Stop"

$ref = if ($env:DIVAN_REF) { $env:DIVAN_REF } else { "v0.12.0" }
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
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ") + "-" + [Guid]::NewGuid().ToString("N").Substring(0, 8)
$work = Join-Path ([IO.Path]::GetTempPath()) ("divan-kur-" + [Guid]::NewGuid())

try {
  New-Item -ItemType Directory -Force -Path $work | Out-Null
  $archiveSha256 = "local-source"
  $sourceCommit = if ($env:DIVAN_SOURCE_COMMIT) { $env:DIVAN_SOURCE_COMMIT } else { "" }
  if ($env:DIVAN_SOURCE_DIR) {
    $source = $env:DIVAN_SOURCE_DIR
    if (-not $sourceCommit) {
      $gitCommit = & git -C $source rev-parse HEAD 2>$null
      if ($LASTEXITCODE -eq 0) { $sourceCommit = ($gitCommit | Select-Object -First 1).Trim() }
    }
    if (-not $sourceCommit) { $sourceCommit = "local-unverified" }
  } else {
    if ($ref -in @("main", "master", "latest")) {
      throw "Degisebilir DIVAN_REF kabul edilmez: $ref"
    }
    $zip = Join-Path $work "divan.zip"
    $checksum = Join-Path $work "divan.sha256"
    $expanded = Join-Path $work "expanded"
    if ($env:DIVAN_ARCHIVE_PATH) {
      Copy-Item -LiteralPath $env:DIVAN_ARCHIVE_PATH -Destination $zip
    } else {
      Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$ref/divan-$ref.zip" -OutFile $zip
    }
    if ($env:DIVAN_ARCHIVE_SHA256) {
      $expectedSha256 = $env:DIVAN_ARCHIVE_SHA256.Trim().ToLowerInvariant()
    } else {
      Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$ref/divan-$ref.sha256" -OutFile $checksum
      $checksumLines = @(Get-Content -LiteralPath $checksum)
      $expectedSha256 = (($checksumLines[0] -split "\s+")[0]).Trim().ToLowerInvariant()
      if (-not $sourceCommit) {
        $commitLine = $checksumLines | Where-Object { $_ -match '^source_commit=' } | Select-Object -First 1
        if ($commitLine) { $sourceCommit = $commitLine.Substring("source_commit=".Length).Trim() }
      }
    }
    if ($expectedSha256 -notmatch '^[0-9a-f]{64}$') {
      throw "Gecersiz SHA-256 kaydi: $expectedSha256"
    }
    $archiveSha256 = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archiveSha256 -ne $expectedSha256) {
      throw "SHA-256 uyusmazligi: beklenen $expectedSha256, bulunan $archiveSha256"
    }
    if (-not $sourceCommit) { $sourceCommit = $ref }
    Expand-Archive $zip -DestinationPath $expanded
    $source = (Get-ChildItem $expanded -Directory | Select-Object -First 1).FullName
  }

  if (-not (Test-Path (Join-Path $source "plugins"))) {
    throw "Divan kaynagi bulunamadi: $source"
  }

  New-Item -ItemType Directory -Force -Path $dst, $stateDir | Out-Null
  $versionFile = Join-Path $source "VERSION"
  $version = if (Test-Path -LiteralPath $versionFile -PathType Leaf) {
    (Get-Content -LiteralPath $versionFile -Raw).Trim()
  } else {
    $ref.TrimStart("v")
  }
  $installedAt = (Get-Date).ToUniversalTime().ToString("o")
  $backupRoot = Join-Path $stateDir "divan-backups\$stamp"
  $manifest = Join-Path $stateDir "divan-install-$stamp.tsv"
  "skill`thedef`tyedek`tsurum`tref`tsource_commit`tarchive_sha256`tinstalled_at" | Set-Content -Encoding utf8 $manifest
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
    "$name`t$target`t$backup`t$version`t$ref`t$sourceCommit`t$archiveSha256`t$installedAt" | Add-Content -Encoding utf8 $manifest
    Write-Host "  vezir: $name"
  }

  $manifest | Set-Content -Encoding utf8 (Join-Path $stateDir "divan-install-latest")
  Write-Host ""
  Write-Host "Divan kuruldu -> $dst"
  Write-Host "Kurulum kaydi -> $manifest"
  Write-Host "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
} finally {
  if (Test-Path $work) { Remove-Item $work -Recurse -Force }
}
