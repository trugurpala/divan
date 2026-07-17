#!/usr/bin/env bash
# Divan'i Codex icin kurar (macOS/Linux)
# Kullanim: curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.sh | bash
set -e
SRC=$(mktemp -d)
curl -fsSL https://github.com/trugurpala/divan/archive/refs/heads/main.tar.gz | tar xz -C "$SRC"
DST="$HOME/.codex/skills"
mkdir -p "$DST"
for d in "$SRC"/divan-main/plugins/*/skills/*/; do
  cp -r "$d" "$DST/" && echo "  vezir: $(basename "$d")"
done
rm -rf "$SRC"
echo ""
echo "Divan kuruldu -> $DST"
echo "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
