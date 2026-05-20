#!/bin/bash
# Local deploy pipeline: lint, build, upload to R2, smoke test, then push.
#
# Usage:
#   bash scripts/deploy.sh          # full deploy
#   bash scripts/deploy.sh --dry-run # skip R2 upload and git push
#
# Prerequisites:
#   - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY available — either exported
#     in the shell, or sitting in .env.local at the repo root (this script
#     auto-sources .env.local when present, so saving keys there once is
#     enough).
#   - Current branch has commits ready to push

set -euo pipefail

# Auto-source .env.local so credentials kept there are picked up without
# the operator having to remember to `export` them every shell.
if [ -f .env.local ]; then
  set -a
  # shellcheck disable=SC1091
  source .env.local
  set +a
fi

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "=== DRY RUN MODE ==="
  echo ""
fi

R2_BASE="https://static.qualibact.org"

# Smoke test URLs — a representative sample of key files
SMOKE_URLS=(
  "$R2_BASE/static/summary/filtered_metrics.csv"
  "$R2_BASE/static/summary/species_counts.csv"
  "$R2_BASE/static/species/Escherichia_coli/qualibact-v1.0/Escherichia_coli_CDS_vs_Genome_Size.png"
  "$R2_BASE/static/species/Salmonella_enterica/qualibact-v1.0/GC_Content_refseq_histogram_kde.png"
)

step() {
  echo ""
  echo "=== $1 ==="
  echo ""
}

fail() {
  echo ""
  echo "FAILED: $1"
  exit 1
}

# --- Step 1: Lint ---
step "Step 1/5: Linting"
npm run lint || fail "Lint errors found"

# --- Step 2: Build ---
step "Step 2/5: Building"
npm run build || fail "Build failed"

# --- Step 3: Upload to R2 ---
step "Step 3/5: Uploading to R2"
if $DRY_RUN; then
  echo "[DRY-RUN] Skipping R2 upload"
else
  bash scripts/upload-to-r2.sh || fail "R2 upload failed"
fi

# --- Step 4: Smoke test R2 URLs ---
step "Step 4/5: Smoke testing R2 URLs"
if $DRY_RUN; then
  echo "[DRY-RUN] Skipping smoke tests"
else
  for url in "${SMOKE_URLS[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" --head "$url")
    if [[ "$status" == "200" ]]; then
      echo "  OK  $url"
    else
      fail "HTTP $status for $url"
    fi
  done
fi

# --- Step 5: Push ---
step "Step 5/5: Pushing to remote"
BRANCH=$(git branch --show-current)
if $DRY_RUN; then
  echo "[DRY-RUN] Would push $BRANCH to origin"
else
  git push origin "$BRANCH" || fail "Git push failed"
fi

echo ""
echo "=== Deploy complete! ==="
echo "Branch '$BRANCH' pushed. Cloudflare Pages will pick up the build."
