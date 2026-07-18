#!/usr/bin/env bash
# Divan Kaldirici — tek komutla geri alma: Claude Code paketleri + pazar kaydi
# ve Codex kurulum kaydindaki skill'ler (varsa yedekler geri yuklenir).
set -Eeuo pipefail

REPO_URL="https://github.com/trugurpala/divan"
RAW_URL="https://raw.githubusercontent.com/trugurpala/divan"
REF="${DIVAN_REF:-main}"
PAKETLER=(sadrazam core-pack ui-pack react-pack zanaat-pack)

WORK=""
BULUNAN=0

temizle() { if [[ -n "$WORK" ]]; then rm -rf "$WORK"; fi; }
trap temizle EXIT

claude_kaldir() {
  command -v claude >/dev/null 2>&1 || return 0
  BULUNAN=1
  echo "-- Claude Code --"
  local paket
  for paket in "${PAKETLER[@]}"; do
    if claude plugin uninstall "$paket@divan"; then
      echo "  paket kaldirildi: $paket"
    else
      echo "  paket kaldirilamadi (kurulu olmayabilir): $paket"
    fi
  done
  if claude plugin marketplace remove divan; then
    echo "  pazar kaydi silindi: divan"
  else
    echo "  pazar kaydi silinemedi (kayitli olmayabilir)"
  fi
}

codex_kaldir() {
  local state_dir="${DIVAN_STATE_DIR:-$HOME/.codex}"
  local kayit_var=0
  if [[ -f "$state_dir/divan-install-latest" ]]; then
    kayit_var=1
  else
    shopt -s nullglob
    local adaylar=("$state_dir"/divan-install-*.tsv)
    shopt -u nullglob
    if ((${#adaylar[@]} > 0)); then kayit_var=1; fi
  fi
  if [[ "$kayit_var" -eq 0 ]]; then return 0; fi
  BULUNAN=1
  echo "-- Codex --"
  local betik=""
  if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    local betik_dizini
    betik_dizini="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$betik_dizini/kaldir-codex.sh" ]]; then
      betik="$betik_dizini/kaldir-codex.sh"
    fi
  fi
  if [[ -z "$betik" ]]; then
    WORK="$(mktemp -d "${TMPDIR:-/tmp}/divan-kaldir.XXXXXX")"
    betik="$WORK/kaldir-codex.sh"
    if ! curl -fsSL "$RAW_URL/$REF/scripts/kaldir-codex.sh" -o "$betik"; then
      echo "  HATA: kaldir-codex.sh indirilemedi. Elle yol: $REPO_URL/wiki/Kaldirma" >&2
      return 1
    fi
  fi
  if ! bash "$betik"; then
    echo "  HATA: Codex kaldirma tamamlanamadi." >&2
    return 1
  fi
}

main() {
  local hata=0
  echo "== Divan Kaldirici =="
  claude_kaldir || hata=1
  codex_kaldir || hata=1
  echo
  if [[ "$BULUNAN" -eq 0 ]]; then
    echo "Divan kurulumu bulunamadi; kaldirilacak bir sey yok."
    echo "Ayrintili rehber: $REPO_URL/wiki/Kaldirma"
  elif [[ "$hata" -eq 0 ]]; then
    echo "Divan kaldirildi. Projelerindeki .divan/, AGENTS.md, BLUEPRINT.md"
    echo "dosyalari sana aittir; istersen elle sil ($REPO_URL/wiki/Kaldirma)."
  fi
  return "$hata"
}

main "$@"
