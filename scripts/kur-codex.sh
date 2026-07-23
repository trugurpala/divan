#!/usr/bin/env bash
echo "scripts/kur-codex.sh is deprecated; use install_codex.sh" >&2
exec "$(dirname "$0")/install_codex.sh" "$@"
