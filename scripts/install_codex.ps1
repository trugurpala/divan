# Canonical Windows fallback installer for Codex.
# DIVAN_REF ile bir tag/commit, CODEX_SKILLS_DIR ile hedef sabitlenebilir.
$ErrorActionPreference = "Stop"

$ref = if ($env:DIVAN_REF) { $env:DIVAN_REF } else { "v0.15.0" }
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
    $downloadedRelease = -not [bool]$env:DIVAN_ARCHIVE_PATH
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
    if ($downloadedRelease) {
      $remoteRefs = @(& git ls-remote https://github.com/trugurpala/divan.git "refs/tags/$ref" "refs/tags/$ref^{}")
      if ($LASTEXITCODE -ne 0 -or -not $remoteRefs) { throw "Etiket commit'i dogrulanamadi: $ref" }
      $peeled = $remoteRefs | Where-Object { $_ -match '\^\{\}$' } | Select-Object -First 1
      $selectedRef = if ($peeled) { $peeled } else { $remoteRefs[0] }
      $tagCommit = ($selectedRef -split "`t")[0].Trim().ToLowerInvariant()
      if ($tagCommit -ne $sourceCommit.Trim().ToLowerInvariant()) {
        throw "Etiket/source_commit uyusmazligi: $tagCommit != $sourceCommit"
      }
    }
    Expand-Archive $zip -DestinationPath $expanded
    $source = (Get-ChildItem $expanded -Directory | Select-Object -First 1).FullName
  }

  if (-not (Test-Path (Join-Path $source "plugins"))) {
    throw "Divan kaynagi bulunamadi: $source"
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if (-not $python) { throw "Python 3 bulunamadi; guvenli kurulum kaydi uretilemiyor." }
  $legacyState = Join-Path $source "scripts\legacy_state.py"
  if (-not (Test-Path -LiteralPath $legacyState -PathType Leaf)) {
    throw "Legacy durum yardimcisi bulunamadi: $legacyState"
  }

  New-Item -ItemType Directory -Force -Path $dst, $stateDir | Out-Null
  $versionFile = Join-Path $source "VERSION"
  $version = if (Test-Path -LiteralPath $versionFile -PathType Leaf) {
    (Get-Content -LiteralPath $versionFile -Raw).Trim()
  } else {
    $ref.TrimStart("v")
  }
  $installedAt = (Get-Date).ToUniversalTime().ToString("o")
  & $python.Source $legacyState install --source $source --skills-dir $dst --state-dir $stateDir `
    --version $version --ref $ref --source-commit $sourceCommit `
    --archive-sha256 $archiveSha256 --installed-at $installedAt
  if ($LASTEXITCODE -ne 0) { throw "Islemsel fallback kurulumu geri alindi." }
  Write-Host ""
  Write-Host "Divan kuruldu -> $dst"
  Write-Host "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
} finally {
  if (Test-Path $work) { Remove-Item $work -Recurse -Force }
}
