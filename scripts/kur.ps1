# Divan Kurucusu — tek komutla Claude Code (masaustu + CLI) ve Codex icin
# Divan'i bu bilgisayara global kurar (Windows). Once ne yapacagini soyler;
# soru sormaz. Istege bagli ayarlar: DIVAN_REF, DIVAN_SOURCE_DIR,
# CODEX_SKILLS_DIR, DIVAN_STATE_DIR — Codex tarafinda kur-codex betigine gecer.
# NOT: 'irm | iex' ile calisir; bu yuzden asla 'exit' kullanilmaz (konsolu
# kapatirdi), hatalar 'throw' ile bildirilir.
function Invoke-DivanKurucu {
  $ErrorActionPreference = "Stop"
  $ProgressPreference = "SilentlyContinue"
  try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
  } catch {}

  $repo = "trugurpala/divan"
  $repoUrl = "https://github.com/trugurpala/divan"
  $ref = if ($env:DIVAN_REF) { $env:DIVAN_REF } else { "main" }
  $paketler = @("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")

  function Invoke-ClaudeCli {
    param([string[]]$Arglar)
    $ErrorActionPreference = "Continue"
    # Out-Host: cikti donus degerine karismasin; yalniz basari durumu donsun.
    & claude @Arglar | Out-Host
    return ($LASTEXITCODE -eq 0)
  }

  # --- Tespit (indirmeden ONCE) ---
  $claudeDurum = "yok"   # yok | var | tam | hata
  $codexDurum = "yok"
  $masaustu = $false
  if (Get-Command claude -ErrorAction SilentlyContinue) {
    $claudeDurum = "var"
  } elseif (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
    $masaustu = $true
  }
  $codexKomut = $null -ne (Get-Command codex -ErrorAction SilentlyContinue)
  $codexDizin = Test-Path (Join-Path $env:USERPROFILE ".codex")
  $codexNiyet = [bool]$env:CODEX_SKILLS_DIR -or [bool]$env:DIVAN_STATE_DIR
  if ($codexKomut -or $codexDizin -or $codexNiyet) { $codexDurum = "var" }

  # --- Banner ---
  Write-Host "== Divan Kurucusu =="
  Write-Host "Divan: vibe coder'in vezirler kurulu — 5 paket, 41 skill. Fermanini"
  Write-Host "verirsin; isi bastan sona planlar, uygular, test eder, kayda gecirir."
  Write-Host ""
  Write-Host "Tespit:"
  if ($claudeDurum -eq "var") {
    Write-Host "  - Claude Code CLI: var (masaustu uygulamasiyla ayni ~/.claude kurulumunu paylasir)"
  } elseif ($masaustu) {
    Write-Host "  - Claude Code CLI: yok; ~/.claude bulundu (yalniz masaustu kullaniyorsun)"
  } else {
    Write-Host "  - Claude Code: yok"
  }
  if ($codexDurum -eq "var") { Write-Host "  - Codex: var" } else { Write-Host "  - Codex: yok" }
  Write-Host ""
  Write-Host "Yapilacaklar: bulunan her araca Divan GLOBAL kurulacak. Ayni adli mevcut"
  Write-Host "skill'ler silinmez; tarihli yedege tasinir ve kurulum kaydi tutulur."
  Write-Host "Geri alma tek komuttur: $repoUrl/wiki/Kaldirma"

  if (($claudeDurum -eq "yok") -and (-not $masaustu) -and ($codexDurum -eq "yok")) {
    Write-Host ""
    Write-Host "Bu bilgisayarda Claude Code veya Codex bulunamadi; Divan'in kurulacagi"
    Write-Host "bir ajan gerekli. Once birini kur, YENI bir PowerShell penceresi ac ve"
    Write-Host "bu komutu tekrar calistir:"
    Write-Host ""
    Write-Host "  Claude Code (Windows):  irm https://claude.ai/install.ps1 | iex"
    Write-Host "  Codex CLI:              https://github.com/openai/codex"
    Write-Host ""
    Write-Host "Ayrintili rehber: $repoUrl/wiki/Kurulum"
    throw "Divan kurulmadi: uygun ajan bulunamadi."
  }

  # --- Claude Code (CLI) ---
  if ($claudeDurum -eq "var") {
    Write-Host ""
    Write-Host "-- Claude Code (global; CLI + masaustu) --"
    if (Invoke-ClaudeCli @("plugin", "marketplace", "add", $repo)) {
      Write-Host "  pazar eklendi: divan"
    } else {
      Write-Host "  pazar zaten kayitli olabilir; guncelleme deneniyor"
      if (-not (Invoke-ClaudeCli @("plugin", "marketplace", "update", "divan"))) {
        Write-Host "  HATA: divan pazari eklenemedi/guncellenemedi."
        $claudeDurum = "hata"
      }
    }
    if ($claudeDurum -eq "var") {
      $basarisiz = @()
      foreach ($paket in $paketler) {
        $tamam = Invoke-ClaudeCli @("plugin", "install", "$paket@divan", "--scope", "user")
        if (-not $tamam) {
          $tamam = Invoke-ClaudeCli @("plugin", "install", "$paket@divan", "--scope", "user")
        }
        if ($tamam) {
          Write-Host "  paket kuruldu: $paket"
        } else {
          Write-Host "  PAKET KURULAMADI: $paket"
          $basarisiz += $paket
        }
      }
      if ($basarisiz.Count -gt 0) {
        $claudeDurum = "hata"
        Write-Host "  Kurulamayanlari Claude Code icinden elle deneyebilirsin:"
        foreach ($paket in $basarisiz) { Write-Host "    /plugin install $paket@divan" }
      } else {
        $claudeDurum = "tam"
      }
    }
  } elseif ($masaustu) {
    Write-Host ""
    Write-Host "-- Claude masaustu uygulamasi --"
    Write-Host "  'claude' komutu PATH'te yok; kurulum uygulamanin icinden yapilir."
    Write-Host "  Claude sohbetine su satirlari sirayla yapistir:"
    Write-Host ""
    Write-Host "    /plugin marketplace add $repo"
    foreach ($paket in $paketler) { Write-Host "    /plugin install $paket@divan" }
    Write-Host ""
    Write-Host "  Istersen once CLI kur; YENI bir PowerShell acip bu betigi tekrar calistir:"
    Write-Host "    irm https://claude.ai/install.ps1 | iex"
  }

  # --- Codex ---
  $work = $null
  if ($codexDurum -eq "var") {
    Write-Host ""
    Write-Host "-- Codex (global skill dizini) --"
    $src = $null
    if ($env:DIVAN_SOURCE_DIR) {
      $src = $env:DIVAN_SOURCE_DIR
    } elseif ($PSCommandPath) {
      $betikDizini = Split-Path -Parent $PSCommandPath
      $kokAdayi = Split-Path -Parent $betikDizini
      if ((Test-Path (Join-Path $betikDizini "kur-codex.ps1")) -and (Test-Path (Join-Path $kokAdayi "plugins"))) {
        $src = $kokAdayi
      }
    }
    try {
      if (-not $src) {
        $work = Join-Path ([IO.Path]::GetTempPath()) ("divan-kurucu-" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
        New-Item -ItemType Directory -Force -Path $work | Out-Null
        $zip = Join-Path $work "divan.zip"
        $expanded = Join-Path $work "expanded"
        Write-Host "  kaynak indiriliyor: $repoUrl ($ref)"
        Invoke-WebRequest -UseBasicParsing "$repoUrl/archive/$ref.zip" -OutFile $zip
        Expand-Archive $zip -DestinationPath $expanded
        $src = (Get-ChildItem $expanded -Directory | Select-Object -First 1).FullName
      }
      if (-not (Test-Path (Join-Path $src "plugins"))) { throw "Divan kaynagi gecersiz: $src" }
      # Arsivin KENDI kur-codex kopyasi calisir; betik ve icerik ayni surum kalir.
      $oncekiKaynak = $env:DIVAN_SOURCE_DIR
      $env:DIVAN_SOURCE_DIR = $src
      try {
        & (Join-Path $src "scripts\kur-codex.ps1")
        $codexDurum = "tam"
      } finally {
        # 'iex' altinda env kalicidir; eski degeri geri koy.
        if ($null -ne $oncekiKaynak) { $env:DIVAN_SOURCE_DIR = $oncekiKaynak }
        else { Remove-Item Env:DIVAN_SOURCE_DIR -ErrorAction SilentlyContinue }
      }
    } catch {
      $codexDurum = "hata"
      Write-Host "  HATA: Codex kurulumu tamamlanamadi: $($_.Exception.Message)"
    } finally {
      if ($work -and (Test-Path $work)) {
        Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
      }
    }
  }

  # --- Ozet ---
  Write-Host ""
  Write-Host "== Ozet =="
  if ($claudeDurum -eq "tam") {
    Write-Host "  Claude Code: 5 paket global kuruldu; masaustu uygulamasi ayni kurulumu gorur."
  } elseif ($claudeDurum -eq "hata") {
    Write-Host "  Claude Code: kurulum TAMAMLANAMADI (yukaridaki hatalara bak)."
  } elseif ($masaustu) {
    Write-Host "  Claude masaustu: yukaridaki /plugin satirlarini uygulamaya yapistir."
  } else {
    Write-Host "  Claude Code: bulunamadi."
  }
  if ($codexDurum -eq "tam") {
    Write-Host "  Codex: 41 skill global kuruldu; kayit ve yedekler durum dizininde."
  } elseif ($codexDurum -eq "hata") {
    Write-Host "  Codex: kurulum TAMAMLANAMADI (yukaridaki hatalara bak)."
  } else {
    Write-Host "  Codex: bulunamadi."
  }
  Write-Host ""
  Write-Host "Simdi ne yapmali:"
  Write-Host "  1. Ajanini (Claude Code / masaustu / Codex) yeniden baslat."
  Write-Host "  2. Ilk fermanini dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
  Write-Host "  3. Niyet secici ve rehber: https://trugurpala.github.io/divan/#basla"
  Write-Host "Geri alma (tek komut): $repoUrl/wiki/Kaldirma"

  if (($claudeDurum -eq "hata") -or ($codexDurum -eq "hata")) {
    throw "Divan kurulumu kismen basarisiz; yukaridaki hatalari incele."
  }
  if (($claudeDurum -ne "tam") -and ($codexDurum -ne "tam")) {
    throw "Divan betikle kurulamadi; yukaridaki masaustu adimlarini uygula."
  }
}

Invoke-DivanKurucu
