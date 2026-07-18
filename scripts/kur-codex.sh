#!/usr/bin/env bash
# Divan'i Codex icin kurar (macOS/Linux).
# DIVAN_REF ile bir tag/commit, CODEX_SKILLS_DIR ile hedef sabitlenebilir.
set -Eeuo pipefail

REF="${DIVAN_REF:-main}"
DST="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
STATE_DIR="${DIVAN_STATE_DIR:-$HOME/.codex}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)-$$"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/divan-kur.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

if [[ -n "${DIVAN_SOURCE_DIR:-}" ]]; then
  SOURCE="$DIVAN_SOURCE_DIR"
else
  SOURCE="$WORK/repo"
  mkdir -p "$SOURCE"
  curl -fsSL "https://github.com/trugurpala/divan/archive/${REF}.tar.gz" \
    | tar xz --strip-components=1 -C "$SOURCE"
fi

if [[ ! -d "$SOURCE/plugins" ]]; then
  echo "HATA: Divan kaynagi bulunamadi: $SOURCE" >&2
  exit 1
fi

mkdir -p "$DST" "$STATE_DIR"
BACKUP_ROOT="$STATE_DIR/divan-backups/$STAMP"
MANIFEST="$STATE_DIR/divan-install-$STAMP.tsv"
printf 'skill\thedef\tyedek\n' > "$MANIFEST"

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
  printf '%s\t%s\t%s\n' "$name" "$target" "$backup" >> "$MANIFEST"
  echo "  vezir: $name"
done

echo
printf '%s\n' "$MANIFEST" > "$STATE_DIR/divan-install-latest"
echo "Divan kuruldu -> $DST"
echo "Kurulum kaydi -> $MANIFEST"
echo "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
