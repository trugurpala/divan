#!/usr/bin/env bash
# Canonical macOS/Linux fallback installer for Codex.
# DIVAN_REF ile bir tag/commit, CODEX_SKILLS_DIR ile hedef sabitlenebilir.
set -Eeuo pipefail

REF="${DIVAN_REF:-v0.14.1}"
DST="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
STATE_DIR="${DIVAN_STATE_DIR:-$HOME/.codex}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/divan-kur.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

ARCHIVE_SHA256="local-source"
SOURCE_COMMIT="${DIVAN_SOURCE_COMMIT:-}"
if [[ -n "${DIVAN_SOURCE_DIR:-}" ]]; then
  SOURCE="$DIVAN_SOURCE_DIR"
  if [[ -z "$SOURCE_COMMIT" ]] && command -v git >/dev/null 2>&1; then
    SOURCE_COMMIT="$(git -C "$SOURCE" rev-parse HEAD 2>/dev/null || true)"
  fi
  SOURCE_COMMIT="${SOURCE_COMMIT:-local-unverified}"
else
  case "$REF" in
    main|master|latest) echo "HATA: Degisebilir DIVAN_REF kabul edilmez: $REF" >&2; exit 1 ;;
  esac
  archive="$WORK/divan.zip"
  checksum="$WORK/divan.sha256"
  expanded="$WORK/expanded"
  downloaded_release=1
  if [[ -n "${DIVAN_ARCHIVE_PATH:-}" ]]; then
    downloaded_release=0
    cp "$DIVAN_ARCHIVE_PATH" "$archive"
  else
    curl -fsSL "https://github.com/trugurpala/divan/releases/download/$REF/divan-$REF.zip" -o "$archive"
  fi
  if [[ -n "${DIVAN_ARCHIVE_SHA256:-}" ]]; then
    expected_sha256="${DIVAN_ARCHIVE_SHA256,,}"
  else
    curl -fsSL "https://github.com/trugurpala/divan/releases/download/$REF/divan-$REF.sha256" -o "$checksum"
    read -r expected_sha256 _ < "$checksum"
    expected_sha256="${expected_sha256,,}"
    if [[ -z "$SOURCE_COMMIT" ]]; then
      SOURCE_COMMIT="$(sed -n 's/^source_commit=//p' "$checksum" | head -n 1)"
    fi
  fi
  if [[ ! "$expected_sha256" =~ ^[0-9a-f]{64}$ ]]; then
    echo "HATA: Gecersiz SHA-256 kaydi: $expected_sha256" >&2
    exit 1
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    ARCHIVE_SHA256="$(sha256sum "$archive" | awk '{print tolower($1)}')"
  elif command -v shasum >/dev/null 2>&1; then
    ARCHIVE_SHA256="$(shasum -a 256 "$archive" | awk '{print tolower($1)}')"
  else
    echo "HATA: SHA-256 araci bulunamadi (sha256sum veya shasum gerekli)." >&2
    exit 1
  fi
  if [[ "$ARCHIVE_SHA256" != "$expected_sha256" ]]; then
    echo "HATA: SHA-256 uyusmazligi: beklenen $expected_sha256, bulunan $ARCHIVE_SHA256" >&2
    exit 1
  fi
  SOURCE_COMMIT="${SOURCE_COMMIT:-$REF}"
  if ((downloaded_release)); then
    remote_refs="$(git ls-remote https://github.com/trugurpala/divan.git "refs/tags/$REF" "refs/tags/$REF^{}")"
    tag_commit="$(printf '%s\n' "$remote_refs" | awk '$2 ~ /\^\{\}$/ {print $1; found=1} END {if (!found) exit 1}' || true)"
    if [[ -z "$tag_commit" ]]; then
      tag_commit="$(printf '%s\n' "$remote_refs" | awk 'NR==1 {print $1}')"
    fi
    if [[ -z "$tag_commit" || "${tag_commit,,}" != "${SOURCE_COMMIT,,}" ]]; then
      echo "HATA: Etiket/source_commit uyusmazligi: ${tag_commit:-missing} != $SOURCE_COMMIT" >&2
      exit 1
    fi
  fi
  mkdir -p "$expanded"
  unzip -q "$archive" -d "$expanded"
  SOURCE="$(find "$expanded" -mindepth 1 -maxdepth 1 -type d -print -quit)"
fi

if [[ ! -d "$SOURCE/plugins" ]]; then
  echo "HATA: Divan kaynagi bulunamadi: $SOURCE" >&2
  exit 1
fi
PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "HATA: Python 3 bulunamadi; guvenli kurulum kaydi uretilemiyor." >&2
  exit 1
fi
LEGACY_STATE="$SOURCE/scripts/legacy_state.py"
if [[ ! -f "$LEGACY_STATE" ]]; then
  echo "HATA: Legacy durum yardimcisi bulunamadi: $LEGACY_STATE" >&2
  exit 1
fi

mkdir -p "$DST" "$STATE_DIR"
if [[ -f "$SOURCE/VERSION" ]]; then
  VERSION="$(tr -d '\r\n' < "$SOURCE/VERSION")"
else
  VERSION="${REF#v}"
fi
INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
"$PYTHON_BIN" "$LEGACY_STATE" install --source "$SOURCE" --skills-dir "$DST" \
  --state-dir "$STATE_DIR" --version "$VERSION" --ref "$REF" \
  --source-commit "$SOURCE_COMMIT" --archive-sha256 "$ARCHIVE_SHA256" \
  --installed-at "$INSTALLED_AT"
echo
echo "Divan kuruldu -> $DST"
echo "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
