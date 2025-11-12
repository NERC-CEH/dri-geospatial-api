#!/bin/sh
echo "Initializing localstack services"

echo "########### Creating geospatial data bucket ###########"
awslocal s3api create-bucket --bucket ukceh-fdri-staging-geospatial --region eu-west-2 --create-bucket-configuration LocationConstraint=eu-west-2

echo "########### Load the raster data into the s3 bucket #########"

DATA_BUCKET="ukceh-fdri-staging-geospatial"
LOCAL_DIR="/var/lib/localstack/data/"

# Loop through all raster files in the directory and its subdirectories
find "$LOCAL_DIR" -type f -name "*.tif" | while read -r FILEPATH; do
    # Extract the relative path after the base directory
    RELATIVE_PATH="${FILEPATH#$LOCAL_DIR}"

    # Construct the S3 key
    S3_KEY="raster/$RELATIVE_PATH"

    # Upload the file to the S3 bucket
    awslocal s3api put-object --bucket "$DATA_BUCKET" --key "$S3_KEY" --body "$FILEPATH"
done

echo "########### Load the vector data into the s3 bucket #########"

# Loop through all vector files in the directory and its subdirectories
find "$LOCAL_DIR" -type f -name "*.geojson" | while read -r FILEPATH; do
    # Extract the relative path after the base directory
    RELATIVE_PATH="${FILEPATH#$LOCAL_DIR}"

    # Construct the S3 key
    S3_KEY="vector/$RELATIVE_PATH"
    echo s3 key: $S3_KEY

    # Upload the file to the S3 bucket
    awslocal s3api put-object --bucket "$DATA_BUCKET" --key "$S3_KEY" --body "$FILEPATH"
done
