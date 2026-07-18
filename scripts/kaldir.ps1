# Divan Kaldirici — tek komutla geri alma (Windows): Claude Code paketleri +
# pazar kaydi ve Codex kurulum kaydindaki skill'ler (yedekler geri yuklenir).
# NOT: 'irm | iex' ile calisir; asla 'exit' kullanilmaz, hatalar 'throw' iledir.
function Invoke-DivanKaldirici {
  $ErrorActionPreference = "Stop"
  $ProgressPreference = "SilentlyContinue"
  try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
  } catch {}

  $repoUrl = "https://github.com/trugurpala/divan"
  $rawUrl = "https://raw.githubusercontent.com/trugurpala/divan"
  $ref = if ($env:DIVAN_REF) { $env:DIVAN_REF } else { "main" }
  $paketler = @("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")
  $bulunan = $false
  $hata = $false

  function Invoke-ClaudeCli {
    param([string[]]$Arglar)
    $ErrorActionPreference = "Continue"
    # Out-Host: cikti donus degerine karismasin; yalniz basari durumu donsun.
    & claude @Arglar | Out-Host
    return ($LASTEXITCODE -eq 0)
  }

  Write-Host "== Divan Kaldirici =="

  if (Get-Command claude -ErrorAction SilentlyContinue) {
    $bulunan = $true
    Write-Host "-- Claude Code --"
    foreach ($paket in $paketler) {
      if (Invoke-ClaudeCli @("plugin", "uninstall", "$paket@divan")) {
        Write-Host "  paket kaldirildi: $paket"
      } else {
        Write-Host "  paket kaldirilamadi (kurulu olmayabilir): $paket"
      }
    }
    if (Invoke-ClaudeCli @("plugin", "marketplace", "remove", "divan")) {
      Write-Host "  pazar kaydi silindi: divan"
    } else {
      Write-Host "  pazar kaydi silinemedi (kayitli olmayabilir)"
    }
  }

  $stateDir = if ($env:DIVAN_STATE_DIR) { $env:DIVAN_STATE_DIR } else { Join-Path $env:USERPROFILE ".codex" }
  $isaretci = Test-Path (Join-Path $stateDir "divan-install-latest")
  $kayitlar = @(Get-ChildItem (Join-Path $stateDir "divan-install-*.tsv") -ErrorAction SilentlyContinue)
  $work = $null
  if ($isaretci -or ($kayitlar.Count -gt 0)) {
    $bulunan = $true
    Write-Host "-- Codex --"
    $betik = $null
    if ($PSCommandPath) {
      $aday = Join-Path (Split-Path -Parent $PSCommandPath) "kaldir-codex.ps1"
      if (Test-Path $aday) { $betik = $aday }
    }
    try {
      if (-not $betik) {
        $work = Join-Path ([IO.Path]::GetTempPath()) ("divan-kaldir-" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
        New-Item -ItemType Directory -Force -Path $work | Out-Null
        $betik = Join-Path $work "kaldir-codex.ps1"
        Invoke-WebRequest -UseBasicParsing "$rawUrl/$ref/scripts/kaldir-codex.ps1" -OutFile $betik
      }
      & $betik
    } catch {
      $hata = $true
      Write-Host "  HATA: Codex kaldirma tamamlanamadi: $($_.Exception.Message)"
    } finally {
      if ($work -and (Test-Path $work)) {
        Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
      }
    }
  }

  Write-Host ""
  if (-not $bulunan) {
    Write-Host "Divan kurulumu bulunamadi; kaldirilacak bir sey yok."
    Write-Host "Ayrintili rehber: $repoUrl/wiki/Kaldirma"
  } elseif (-not $hata) {
    Write-Host "Divan kaldirildi. Projelerindeki .divan/, AGENTS.md, BLUEPRINT.md"
    Write-Host "dosyalari sana aittir; istersen elle sil ($repoUrl/wiki/Kaldirma)."
  }
  if ($hata) { throw "Divan kaldirma kismen basarisiz; yukaridaki hatalari incele." }
}

Invoke-DivanKaldirici
