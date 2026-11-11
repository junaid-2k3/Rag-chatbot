#!/usr/bin/env bash
# Delete everything deploy.sh created (stack, function, logs, bucket and its contents).
set -euo pipefail
export AWS_DEFAULT_REGION="${AWS_REGION:-ap-south-1}"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="fast-pwr-chatbot-${ACCOUNT}-${AWS_DEFAULT_REGION}"
read -r -p "Delete stack fast-pwr-chatbot and bucket $BUCKET? [y/N] " yn
[ "$yn" = "y" ] || exit 1
aws cloudformation delete-stack --stack-name fast-pwr-chatbot
aws cloudformation wait stack-delete-complete --stack-name fast-pwr-chatbot
aws s3 rb "s3://$BUCKET" --force
