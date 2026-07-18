#!/usr/bin/env bash
# Divan Codex kurulum kaydini kullanarak yalniz kayitli hedefleri kaldirir.
set -Eeuo pipefail

DST="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
STATE_DIR="${DIVAN_STATE_DIR:-$HOME/.codex}"
MANIFEST="${1:-}"

if [[ -z "$MANIFEST" ]]; then
  latest="$STATE_DIR/divan-install-latest"
  if [[ -f "$latest" ]]; then
    IFS= read -r MANIFEST < "$latest"
  else
    shopt -s nullglob
    manifests=("$STATE_DIR"/divan-install-*.tsv)
    if ((${#manifests[@]} == 0)); then
      echo "HATA: Divan kurulum kaydi bulunamadi: $STATE_DIR" >&2
      exit 1
    fi
    MANIFEST="${manifests[0]}"
    for candidate in "${manifests[@]}"; do
      [[ "$candidate" -nt "$MANIFEST" ]] && MANIFEST="$candidate"
    done
  fi
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "HATA: Kurulum kaydi bulunamadi: $MANIFEST" >&2
  exit 1
fi

DST="$(cd "$DST" && pwd -P)"
while IFS=$'\t' read -r name target backup; do
  [[ "$name" == "skill" || -z "$name" ]] && continue
  case "$target" in
    "$DST"/*) ;;
    *) echo "HATA: Kayitli hedef skill dizini disinda: $target" >&2; exit 1 ;;
  esac
  if [[ -e "$target" ]]; then
    rm -rf -- "$target"
  fi
  if [[ -n "$backup" && -e "$backup" ]]; then
    mv -- "$backup" "$target"
    echo "  geri yuklendi: $name"
  else
    echo "  kaldirildi: $name"
  fi
done < "$MANIFEST"

echo "Divan kaldirildi; kullanilan kayit korundu -> $MANIFEST"
