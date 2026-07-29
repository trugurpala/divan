#!/usr/bin/env bash
# Canonical macOS/Linux fallback uninstaller for Codex.
set -Eeuo pipefail

DST="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
STATE_DIR="${DIVAN_STATE_DIR:-$HOME/.codex}"
MANIFEST=""
PYTHON_OVERRIDE="${DIVAN_PYTHON:-}"
while (($#)); do
  case "$1" in
    --manifest) MANIFEST="$2"; shift 2 ;;
    --python) PYTHON_OVERRIDE="$2"; shift 2 ;;
    *)
      if [[ -z "$MANIFEST" ]]; then
        MANIFEST="$1"
        shift
      else
        echo "HATA: Bilinmeyen kaldirma argumani: $1" >&2
        exit 2
      fi
      ;;
  esac
done

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

PYTHON_BIN="$PYTHON_OVERRIDE"
if [[ -z "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3 || command -v python || true)"
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "HATA: Python 3 bulunamadi; guvenli kaldirma calistirilamiyor." >&2
  exit 1
fi
"$PYTHON_BIN" "$(dirname "$0")/legacy_state.py" migrate \
  --manifest "$MANIFEST" --skills-dir "$DST" --state-dir "$STATE_DIR"
echo "Divan karantinaya alindi; kullanilan kayit korundu -> $MANIFEST"
