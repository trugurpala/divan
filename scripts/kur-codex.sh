#!/usr/bin/env bash
# Divan'i Codex icin kurar (macOS/Linux).
# DIVAN_REF ile bir tag/commit, CODEX_SKILLS_DIR ile hedef sabitlenebilir.
set -Eeuo pipefail

REF="${DIVAN_REF:-v0.12.0}"
DST="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
STATE_DIR="${DIVAN_STATE_DIR:-$HOME/.codex}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)-$$"
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
  if [[ -n "${DIVAN_ARCHIVE_PATH:-}" ]]; then
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
  mkdir -p "$expanded"
  unzip -q "$archive" -d "$expanded"
  SOURCE="$(find "$expanded" -mindepth 1 -maxdepth 1 -type d -print -quit)"
fi

if [[ ! -d "$SOURCE/plugins" ]]; then
  echo "HATA: Divan kaynagi bulunamadi: $SOURCE" >&2
  exit 1
fi

mkdir -p "$DST" "$STATE_DIR"
if [[ -f "$SOURCE/VERSION" ]]; then
  VERSION="$(tr -d '\r\n' < "$SOURCE/VERSION")"
else
  VERSION="${REF#v}"
fi
INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BACKUP_ROOT="$STATE_DIR/divan-backups/$STAMP"
MANIFEST="$STATE_DIR/divan-install-$STAMP.tsv"
printf 'skill\thedef\tyedek\tsurum\tref\tsource_commit\tarchive_sha256\tinstalled_at\n' > "$MANIFEST"

shopt -s nullglob
skills=("$SOURCE"/plugins/*/skills/*)
if ((${#skills[@]} == 0)); then
  echo "HATA: Kurulacak skill bulunamadi." >&2
  exit 1
fi

seen_names=$'\n'
for skill in "${skills[@]}"; do
  [[ -d "$skill" && -f "$skill/SKILL.md" ]] || continue
  name="$(basename "$skill")"
  if [[ "$seen_names" == *$'\n'"$name"$'\n'* ]]; then
    echo "HATA: Tekrarlanan skill adi: $name" >&2
    exit 1
  fi
  seen_names+="$name"$'\n'

  target="$DST/$name"
  backup=""
  if [[ -e "$target" ]]; then
    backup="$BACKUP_ROOT/$name"
    mkdir -p "$BACKUP_ROOT"
    mv "$target" "$backup"
  fi

  if ! cp -R "$skill" "$target"; then
    [[ -n "$backup" && -e "$backup" ]] && mv "$backup" "$target"
    echo "HATA: $name kopyalanamadi; onceki surum geri getirildi." >&2
    exit 1
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$name" "$target" "$backup" "$VERSION" "$REF" "$SOURCE_COMMIT" "$ARCHIVE_SHA256" "$INSTALLED_AT" >> "$MANIFEST"
  echo "  vezir: $name"
done

echo
printf '%s\n' "$MANIFEST" > "$STATE_DIR/divan-install-latest"
echo "Divan kuruldu -> $DST"
echo "Kurulum kaydi -> $MANIFEST"
echo "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
