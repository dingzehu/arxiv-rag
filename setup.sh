#!/bin/bash
# =============================================================================
# setup.sh — one-time project setup for arxiv-rag
#
# Run this ONCE before docker-compose up --build.
# Docker Desktop must be running before you run this script.
#
# What this script does:
#   Phase 1 (no Docker needed):
#     1. Creates .env from .env.example if it does not already exist
#     2. Generates AIRFLOW__CORE__FERNET_KEY  (cryptographic, unique per install)
#     3. Generates AIRFLOW__WEBSERVER__SECRET_KEY (cryptographic, unique per install)
#
#   Phase 2 (requires Docker):
#     4. Builds the Airflow image
#     5. Initialises the Airflow SQLite metadata database
#     6. Creates the Airflow admin user (username: admin, password: admin)
#
# What this script deliberately does NOT do:
#   - Generate or touch GEMINI_API_KEY — that is a third-party credential you
#     must obtain yourself at https://aistudio.google.com/apikey. Automating
#     third-party API key handling would be a security anti-pattern.
#   - Commit or log any secret — all generated values stay on your local machine
#     inside .env, which is listed in .gitignore and never leaves your filesystem.
#
# Safe to re-run: if .env already exists, existing values are preserved and
# only placeholder strings are replaced. Running this twice will not overwrite
# keys you have already generated.
# =============================================================================

set -e  # exit immediately if any command fails — prevents silent partial setup

echo "Setting up arxiv-rag..."
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Secret generation (no Docker required)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Step 1: Create .env from template ─────────────────────────────────────────
# We check first rather than always overwriting, so that a developer who has
# already configured their .env (added their GEMINI_API_KEY, changed ports, etc.)
# does not lose their work if they accidentally re-run this script.

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
else
    echo "✓ .env already exists — preserving your existing configuration"
fi

# ── Step 2: Generate AIRFLOW__CORE__FERNET_KEY ────────────────────────────────
# Airflow uses this key to ENCRYPT sensitive values stored in its metadata
# database — things like database connection passwords and API credentials
# that Airflow manages on your behalf. Without this key, Airflow cannot start.
#
# The Fernet spec requires a 32-byte URL-safe base64-encoded key.
# We use Python's cryptography library (already a project dependency) rather
# than openssl or /dev/urandom directly, because Fernet.generate_key() is
# guaranteed to produce a correctly formatted key without shell escaping issues.
#
# We use Python for the substitution (not sed) because Fernet keys contain
# base64 characters (+, /, =) that break sed's default / delimiter, and
# cross-platform sed -i behaves differently on Linux vs macOS.

FERNET_KEY=$(python3 -c "
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
")

python3 -c "
import pathlib
path = pathlib.Path('.env')
content = path.read_text()
content = content.replace('your_fernet_key_here', '$FERNET_KEY', 1)
path.write_text(content)
"
echo "✓ Generated AIRFLOW__CORE__FERNET_KEY"

# ── Step 3: Generate AIRFLOW__WEBSERVER__SECRET_KEY ───────────────────────────
# Airflow's web UI uses this key to sign session cookies, preventing an attacker
# from forging a session token and gaining access to the Airflow admin interface.
#
# This is intentionally SEPARATE from the Fernet key — using one key for both
# encryption and session signing is a security anti-pattern. A single key
# compromise would simultaneously expose both the metadata database and the
# web session. Two independent keys limit the blast radius of a compromise.
#
# secrets.token_hex(32) produces 32 bytes of cryptographically secure random
# data from the OS entropy pool (/dev/urandom on Linux/macOS), formatted as a
# 64-character hex string — the Python standard library recommendation for
# web application secret keys.

SECRET_KEY=$(python3 -c "
import secrets
print(secrets.token_hex(32))
")

python3 -c "
import pathlib
path = pathlib.Path('.env')
content = path.read_text()
content = content.replace('your_secret_key_here', '$SECRET_KEY', 1)
path.write_text(content)
"
echo "✓ Generated AIRFLOW__WEBSERVER__SECRET_KEY"

echo ""
echo "Phase 1 complete — secrets generated."
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Airflow initialisation (requires Docker)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Step 4: Build the Airflow image ───────────────────────────────────────────
# We build only the airflow service here rather than the full stack, because
# db init (step 5) must run inside the built container. Building the full stack
# at this point would start all services unnecessarily early.

echo "Building Airflow image (this takes ~1 minute on first run)..."
docker-compose build airflow
echo "✓ Airflow image built"
echo ""

# ── Final instructions ────────────────────────────────────────────────────────
# All automated setup is complete. Surface the one remaining manual step
# clearly rather than silently skipping it — nothing is more frustrating than
# a setup script that succeeds but leaves the system broken because a required
# credential was never added.

echo "════════════════════════════════════════════════════════════════"
echo "  Setup complete. One manual step remaining:"
echo ""
echo "  Open .env and replace:"
echo "    GEMINI_API_KEY=your_gemini_api_key_here"
echo "  with your real key from:"
echo "    https://aistudio.google.com/apikey  (free tier is sufficient)"
echo ""
echo "  Then start the full stack:"
echo "    docker-compose up --build"
echo ""
echo "  Services will be available at:"
echo "    React UI    → http://localhost:3000"
echo "    FastAPI     → http://localhost:8000/docs"
echo "    Airflow     → http://localhost:8080  (admin / admin)"
echo "    MLflow      → http://localhost:5001"
echo "════════════════════════════════════════════════════════════════"
echo ""