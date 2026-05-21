#!/bin/bash
# Upload public/static/ and public/api/ to Cloudflare R2 using AWS CLI
# (S3-compatible API).
#
# Prerequisites:
#   1. Create an R2 API token in Cloudflare dashboard (R2 > Manage R2 API Tokens)
#   2. Configure AWS CLI:
#      export AWS_ACCESS_KEY_ID=<your-r2-access-key>
#      export AWS_SECRET_ACCESS_KEY=<your-r2-secret-key>
#   3. Run this script from the project root:
#      bash scripts/upload-to-r2.sh

set -euo pipefail

R2_ENDPOINT="https://3bd272de7abb5a9f328fbfa9afafd2a3.r2.cloudflarestorage.com"
R2_BUCKET="qualibact"

if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
  echo "Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set."
  echo "Create an R2 API token at: Cloudflare Dashboard > R2 > Manage R2 API Tokens"
  exit 1
fi

# Two prefixes get uploaded:
#   public/static/ -> s3://qualibact/static/   (bulk plots, atb tier CSVs,
#                                              refseq archives, assembly stats)
#   public/api/    -> s3://qualibact/api/      (the v2 threshold API blobs
#                                              referenced via staticUrl())
sync_dir() {
  local src="$1"
  local prefix="$2"
  if [ ! -d "$src" ]; then
    echo "Warning: $src not found, skipping."
    return 0
  fi
  echo "Uploading $src -> s3://$R2_BUCKET/$prefix"
  aws s3 sync "$src" "s3://$R2_BUCKET/$prefix" \
    --endpoint-url "$R2_ENDPOINT" \
    --region auto \
    --delete \
    --no-progress \
    --exclude "*.DS_Store"
  echo ""
}

echo "Endpoint: $R2_ENDPOINT"
echo ""

sync_dir "public/static" "static"
sync_dir "public/api" "api"

echo "Upload complete!"
echo "Files are at: s3://$R2_BUCKET/static/ and s3://$R2_BUCKET/api/"
echo ""
echo "Reminders:"
echo "  1. R2 bucket public access must be enabled (Cloudflare Dashboard > R2)."
echo "  2. NEXT_PUBLIC_STATIC_URL=https://static.qualibact.org points the site at it."
echo "  3. CORS on the bucket (Settings > CORS Policy):"
echo "       Allowed Origins: https://qualibact.org"
echo "       Allowed Methods: GET, HEAD"
echo "       Allowed Headers: *"
