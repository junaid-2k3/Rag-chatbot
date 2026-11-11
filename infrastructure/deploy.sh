#!/usr/bin/env bash
# Deploy the backend to AWS. Needs: AWS CLI configured, uv, zip, and GEMINI_API_KEY in .env.
#   ALLOWED_ORIGINS=https://<user>.github.io ./infrastructure/deploy.sh
# Uploads the index, embedding model and code to a private S3 bucket, then creates/updates the stack.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${ALLOWED_ORIGINS:?set ALLOWED_ORIGINS to the GitHub Pages origin, e.g. https://user.github.io}"
export AWS_DEFAULT_REGION="${AWS_REGION:-ap-south-1}"
STACK=fast-pwr-chatbot

set -a; [ -f .env ] && . ./.env; set +a
: "${GEMINI_API_KEY:?GEMINI_API_KEY missing in .env}"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="fast-pwr-chatbot-${ACCOUNT}-${AWS_DEFAULT_REGION}"
echo "account $ACCOUNT, region $AWS_DEFAULT_REGION, bucket $BUCKET"

if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" \
    --create-bucket-configuration "LocationConstraint=$AWS_DEFAULT_REGION" >/dev/null
fi
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration \
  '{"Rules":[{"ID":"expire-old-code","Status":"Enabled","Filter":{"Prefix":"code/"},"Expiration":{"Days":14}}]}'

aws s3 sync index "s3://$BUCKET/index" --delete --only-show-errors
aws s3 cp models/bge-small/tokenizer.json "s3://$BUCKET/models/bge-small/tokenizer.json" --only-show-errors
aws s3 cp models/bge-small/onnx/model.onnx "s3://$BUCKET/models/bge-small/onnx/model.onnx" --only-show-errors

./infrastructure/build_zip.sh
KEY="code/lambda-$(sha256sum build/lambda.zip | cut -c1-12).zip"
aws s3 cp build/lambda.zip "s3://$BUCKET/$KEY" --only-show-errors

aws cloudformation deploy --stack-name "$STACK" --template-file infrastructure/template.yaml \
  --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
  --parameter-overrides "BucketName=$BUCKET" "CodeKey=$KEY" \
  "AllowedOrigins=$ALLOWED_ORIGINS" "GeminiApiKey=$GEMINI_API_KEY"

URL=$(aws cloudformation describe-stacks --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='FunctionUrl'].OutputValue" --output text)
echo "Function URL: $URL"
echo "Set it as the PUBLIC_API_URL repository variable for the frontend build."
