#!/usr/bin/env bash
# Divan Kurucusu — tek komutla Claude Code (masaustu + CLI) ve Codex icin
# Divan'i bu bilgisayara global kurar. Once ne yapacagini soyler; soru sormaz.
# Istege bagli ayarlar: DIVAN_REF (surum sabitleme), DIVAN_SOURCE_DIR,
# CODEX_SKILLS_DIR, DIVAN_STATE_DIR — Codex tarafinda kur-codex betigine gecer.
set -Eeuo pipefail

REPO="trugurpala/divan"
REPO_URL="https://github.com/trugurpala/divan"
REF="${DIVAN_REF:-main}"
PAKETLER=(sadrazam core-pack ui-pack react-pack zanaat-pack)

WORK=""
SRC=""
CLAUDE_DURUM="yok"   # yok | var | tam | hata
CODEX_DURUM="yok"    # yok | var | tam | hata
MASAUSTU=0

temizle() { if [[ -n "$WORK" ]]; then rm -rf "$WORK"; fi; }
trap temizle EXIT

tespit() {
  if command -v claude >/dev/null 2>&1; then
    CLAUDE_DURUM="var"
  elif [[ -d "$HOME/.claude" ]]; then
    MASAUSTU=1
  fi
  # CODEX_SKILLS_DIR/DIVAN_STATE_DIR'in elle verilmesi acik niyettir (CI dahil).
  if command -v codex >/dev/null 2>&1 || [[ -d "$HOME/.codex" ]] \
    || [[ -n "${CODEX_SKILLS_DIR:-}" || -n "${DIVAN_STATE_DIR:-}" ]]; then
    CODEX_DURUM="var"
  fi
}

banner() {
  echo "== Divan Kurucusu =="
  echo "Divan: vibe coder'in vezirler kurulu — 5 paket, 41 skill. Fermanini"
  echo "verirsin; isi bastan sona planlar, uygular, test eder, kayda gecirir."
  echo
  echo "Tespit:"
  if [[ "$CLAUDE_DURUM" == "var" ]]; then
    echo "  - Claude Code CLI: var (masaustu uygulamasiyla ayni ~/.claude kurulumunu paylasir)"
  elif [[ "$MASAUSTU" -eq 1 ]]; then
    echo "  - Claude Code CLI: yok; ~/.claude bulundu (yalniz masaustu kullaniyorsun)"
  else
    echo "  - Claude Code: yok"
  fi
  if [[ "$CODEX_DURUM" == "var" ]]; then
    echo "  - Codex: var"
  else
    echo "  - Codex: yok"
  fi
  echo
  echo "Yapilacaklar: bulunan her araca Divan GLOBAL kurulacak. Ayni adli mevcut"
  echo "skill'ler silinmez; tarihli yedege tasinir ve kurulum kaydi tutulur."
  echo "Geri alma tek komuttur: $REPO_URL/wiki/Kaldirma"
}

claude_kur() {
  echo
  echo "-- Claude Code (global; CLI + masaustu) --"
  if claude plugin marketplace add "$REPO"; then
    echo "  pazar eklendi: divan"
  else
    echo "  pazar zaten kayitli olabilir; guncelleme deneniyor"
    if ! claude plugin marketplace update divan; then
      echo "  HATA: divan pazari eklenemedi/guncellenemedi." >&2
      CLAUDE_DURUM="hata"
      return 0
    fi
  fi
  local basarisiz=()
  local paket
  for paket in "${PAKETLER[@]}"; do
    if claude plugin install "$paket@divan" --scope user \
      || claude plugin install "$paket@divan" --scope user; then
      echo "  paket kuruldu: $paket"
    else
      echo "  PAKET KURULAMADI: $paket" >&2
      basarisiz+=("$paket")
    fi
  done
  if ((${#basarisiz[@]} > 0)); then
    CLAUDE_DURUM="hata"
    echo "  Kurulamayanlari Claude Code icinden elle deneyebilirsin:" >&2
    for paket in "${basarisiz[@]}"; do
      echo "    /plugin install $paket@divan" >&2
    done
  else
    CLAUDE_DURUM="tam"
  fi
}

masaustu_bilgi() {
  echo
  echo "-- Claude masaustu uygulamasi --"
  echo "  'claude' komutu PATH'te yok; kurulum uygulamanin icinden yapilir."
  echo "  Claude sohbetine su satirlari sirayla yapistir:"
  echo
  echo "    /plugin marketplace add $REPO"
  local paket
  for paket in "${PAKETLER[@]}"; do
    echo "    /plugin install $paket@divan"
  done
  echo
  echo "  Istersen once CLI kur; YENI bir terminal acip bu betigi tekrar calistir:"
  echo "    curl -fsSL https://claude.ai/install.sh | bash"
}

kaynak_hazirla() {
  if [[ -n "${DIVAN_SOURCE_DIR:-}" ]]; then
    SRC="$DIVAN_SOURCE_DIR"
  elif [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    local betik_dizini
    betik_dizini="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$betik_dizini/kur-codex.sh" && -d "$betik_dizini/../plugins" ]]; then
      SRC="$(cd "$betik_dizini/.." && pwd)"
    fi
  fi
  if [[ -z "$SRC" ]]; then
    WORK="$(mktemp -d "${TMPDIR:-/tmp}/divan-kurucu.XXXXXX")"
    SRC="$WORK/repo"
    mkdir -p "$SRC"
    echo "  kaynak indiriliyor: $REPO_URL ($REF)"
    if ! curl -fsSL "$REPO_URL/archive/${REF}.tar.gz" | tar xz --strip-components=1 -C "$SRC"; then
      echo "  HATA: kaynak indirilemedi (ag/proxy?). Elle kurulum: $REPO_URL/wiki/Kurulum" >&2
      SRC=""
      return 1
    fi
  fi
  if [[ ! -d "$SRC/plugins" ]]; then
    echo "  HATA: Divan kaynagi gecersiz: $SRC" >&2
    SRC=""
    return 1
  fi
}

codex_kur() {
  echo
  echo "-- Codex (global skill dizini) --"
  if ! kaynak_hazirla; then
    CODEX_DURUM="hata"
    return 0
  fi
  # Arsivin KENDI kur-codex kopyasi calisir; betik ve icerik ayni surum kalir.
  if DIVAN_SOURCE_DIR="$SRC" bash "$SRC/scripts/kur-codex.sh"; then
    CODEX_DURUM="tam"
  else
    CODEX_DURUM="hata"
    echo "  HATA: Codex kurulumu tamamlanamadi." >&2
  fi
}

hicbiri_bulunamadi() {
  echo
  echo "Bu bilgisayarda Claude Code veya Codex bulunamadi; Divan'in kurulacagi"
  echo "bir ajan gerekli. Once birini kur, YENI bir terminal ac ve bu komutu"
  echo "tekrar calistir:"
  echo
  echo "  Claude Code (macOS/Linux):  curl -fsSL https://claude.ai/install.sh | bash"
  echo "  Claude Code (Windows):      irm https://claude.ai/install.ps1 | iex"
  echo "  Codex CLI:                  https://github.com/openai/codex"
  echo
  echo "Ayrintili rehber: $REPO_URL/wiki/Kurulum"
}

ozet() {
  echo
  echo "== Ozet =="
  case "$CLAUDE_DURUM" in
    tam) echo "  Claude Code: 5 paket global kuruldu; masaustu uygulamasi ayni kurulumu gorur." ;;
    hata) echo "  Claude Code: kurulum TAMAMLANAMADI (yukaridaki hatalara bak)." ;;
    *)
      if [[ "$MASAUSTU" -eq 1 ]]; then
        echo "  Claude masaustu: yukaridaki /plugin satirlarini uygulamaya yapistir."
      else
        echo "  Claude Code: bulunamadi."
      fi
      ;;
  esac
  case "$CODEX_DURUM" in
    tam) echo "  Codex: 41 skill global kuruldu; kayit ve yedekler durum dizininde." ;;
    hata) echo "  Codex: kurulum TAMAMLANAMADI (yukaridaki hatalara bak)." ;;
    *) echo "  Codex: bulunamadi." ;;
  esac
  echo
  echo "Simdi ne yapmali:"
  echo "  1. Ajanini (Claude Code / masaustu / Codex) yeniden baslat."
  echo "  2. Ilk fermanini dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
  echo "  3. Niyet secici ve rehber: https://trugurpala.github.io/divan/#basla"
  echo "Geri alma (tek komut): $REPO_URL/wiki/Kaldirma"
}

main() {
  tespit
  banner
  if [[ "$CLAUDE_DURUM" == "yok" && "$MASAUSTU" -eq 0 && "$CODEX_DURUM" == "yok" ]]; then
    hicbiri_bulunamadi
    return 1
  fi
  if [[ "$CLAUDE_DURUM" == "var" ]]; then
    claude_kur
  elif [[ "$MASAUSTU" -eq 1 ]]; then
    masaustu_bilgi
  fi
  if [[ "$CODEX_DURUM" == "var" ]]; then
    codex_kur
  fi
  ozet
  if [[ "$CLAUDE_DURUM" == "hata" || "$CODEX_DURUM" == "hata" ]]; then
    return 1
  fi
  if [[ "$CLAUDE_DURUM" == "tam" || "$CODEX_DURUM" == "tam" ]]; then
    return 0
  fi
  # Yalniz masaustu yol gosterildi; betik kendi basina kurulum yapamadi.
  return 1
}

main "$@"
