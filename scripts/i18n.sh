#!/usr/bin/env bash
set -euo pipefail

# Project root: directory containing manage.py
ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

# Ensure gettext is available (macOS tip)
if ! command -v xgettext >/dev/null 2>&1; then
  echo "GNU gettext tools not found. On macOS:"
  echo "  brew install gettext && brew link --force gettext"
  echo "Or add to PATH: export PATH=\"/opt/homebrew/opt/gettext/bin:$PATH\""
  exit 1
fi

# Languages to manage
LANGS=(ar cs pl)

# Create or update message catalogs
echo "Extracting messages for: ${LANGS[*]}"
python3 manage.py makemessages ${LANGS[@]/#/-l }

# Compile to .mo files
echo "Compiling messages"
python3 manage.py compilemessages

echo "Done. Edit translations in locale/<lang>/LC_MESSAGES/django.po and rerun this script."
