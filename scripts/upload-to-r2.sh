#!/bin/bash
# Upload public/static/ to Cloudflare R2 using AWS CLI (S3-compatible API)
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
SOURCE_DIR="public/static"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: $SOURCE_DIR directory not found. Run from project root."
  exit 1
fi

if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
  echo "Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set."
  echo "Create an R2 API token at: Cloudflare Dashboard > R2 > Manage R2 API Tokens"
  exit 1
fi

echo "Uploading $SOURCE_DIR to R2 bucket: $R2_BUCKET"
echo "Endpoint: $R2_ENDPOINT"
echo ""

# Sync with appropriate content types
aws s3 sync "$SOURCE_DIR" "s3://$R2_BUCKET/static" \
  --endpoint-url "$R2_ENDPOINT" \
  --region auto \
  --delete \
  --no-progress \
  --exclude "*.DS_Store"

echo ""
echo "Upload complete!"
echo "Files are at: s3://$R2_BUCKET/static/"
echo ""
echo "Next steps:"
echo "  1. Enable public access on the R2 bucket in Cloudflare dashboard"
echo "  2. Set NEXT_PUBLIC_STATIC_URL in Vercel to your R2 public URL"
echo "  3. Configure CORS on the R2 bucket (Settings > CORS Policy):"
echo "       Allowed Origins: https://qualibact.org"
echo "       Allowed Methods: GET, HEAD"
echo "       Allowed Headers: *"
