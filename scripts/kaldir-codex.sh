#!/usr/bin/env bash
echo "scripts/kaldir-codex.sh is deprecated; use uninstall_codex.sh" >&2
exec "$(dirname "$0")/uninstall_codex.sh" "$@"
