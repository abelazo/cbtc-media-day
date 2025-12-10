#!/usr/bin/env bash

set -eo pipefail

echo "🔨 Building content service Lambda deployment package..."

# Configuration
SERVICE_NAME="content_service"
DIST_DIR="dist"
ZIP_FILE="${SERVICE_NAME}.zip"
S3_KEY="${SERVICE_NAME}/${ZIP_FILE}"

# Get S3 bucket name from Terraform output
pushd ../../infra/global >& /dev/null
BUCKET_NAME=$(terraform output -raw lambda_sources_bucket_name 2>/dev/null || echo "")
popd >& /dev/null

SKIP_UPLOAD=false
if [ -z "$BUCKET_NAME" ]; then
    echo "⚠️  Warning: Could not get bucket name from Terraform. Skipping upload."
    echo "   Make sure global infrastructure is deployed first."
    SKIP_UPLOAD=true
fi

# Clean up previous build
echo "🧹 Cleaning up previous build..."
rm -rf "$DIST_DIR"

# Create dist directory
echo "📦 Creating dist directory..."
mkdir -p "$DIST_DIR"

# Copy source code
echo "📋 Copying source code..."
cp -r src/* "$DIST_DIR/"

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt -t "$DIST_DIR/" --quiet
else
    echo "ℹ️  No requirements.txt found, skipping dependency installation"
fi

# Create zip file in dist directory
echo "🗜️  Creating zip file..."
cd "$DIST_DIR"
zip -r "$ZIP_FILE" . -q
cd ..

echo "✅ Build complete: $DIST_DIR/$ZIP_FILE"

# Upload to S3 if bucket name is available
if [ "$SKIP_UPLOAD" != "true" ]; then
    echo "☁️  Uploading to S3..."

    # Check if AWS profile is set
    if [ -z "$AWS_PROFILE" ]; then
        echo "⚠️  AWS profile not set. Setting LocalStack defaults..."
        export AWS_ACCESS_KEY_ID=test
        export AWS_SECRET_ACCESS_KEY=test
        export AWS_DEFAULT_REGION=eu-west-1
        export AWS_ENDPOINT_URL=http://localhost:4566
    fi

    # Upload to S3
    aws s3 cp "$DIST_DIR/$ZIP_FILE" "s3://${BUCKET_NAME}/${S3_KEY}" ${AWS_ENDPOINT_URL:+--endpoint-url=$AWS_ENDPOINT_URL}

    echo "✅ Uploaded to s3://${BUCKET_NAME}/${S3_KEY}"
else
    echo "⏭️  Skipping upload"
fi

echo "🎉 Done! Package available at: $DIST_DIR/$ZIP_FILE"
