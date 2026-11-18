#!/usr/bin/env bash
# Build script used by Render (and handy locally for a production check).
#
# bash build.sh
#
# Steps:
#   1. install Python dependencies
#   2. compile the Arabic gettext catalog without external tools
#   3. collect static files for WhiteNoise
#   4. apply database migrations
#   5. create/update the mosque administrator from environment variables

set -o errexit
set -o pipefail
set -o nounset

echo "==> Python $(python --version 2>&1)"

echo "==> Installing dependencies"
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements.txt

echo "==> Compiling translations"
python scripts/compile_po.py

echo "==> Collecting static files"
python manage.py collectstatic --no-input

echo "==> Applying migrations"
python manage.py migrate --no-input

echo "==> Ensuring the administrator account exists"
python manage.py ensure_admin

echo "==> Build complete"
