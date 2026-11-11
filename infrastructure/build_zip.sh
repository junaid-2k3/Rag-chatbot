#!/usr/bin/env bash
# Build build/lambda.zip for Lambda python3.12 on x86_64. boto3 is provided by the runtime.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf build && mkdir -p build/lambda
uv pip install --quiet --target build/lambda \
  --python-version 3.12 --python-platform x86_64-manylinux_2_28 --only-binary=:all: \
  -r backend/requirements-lambda.txt
cp -r backend/app backend/lambda_handler.py build/lambda/
find build/lambda -name __pycache__ -type d -prune -exec rm -rf {} +
(cd build/lambda && zip -qr ../lambda.zip .)
echo "unzipped: $(du -sm build/lambda | cut -f1) MB (limit 250), zipped: $(du -m build/lambda.zip | cut -f1) MB"
