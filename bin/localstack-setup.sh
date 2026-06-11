#!/bin/sh
echo "Initializing localstack services"

echo "########### Creating geospatial data bucket ###########"
awslocal s3api create-bucket --bucket ukceh-fdri-staging-geospatial --region eu-west-2 --create-bucket-configuration LocationConstraint=eu-west-2


echo "########### Load the sample data into the s3 bucket #########"

awslocal s3api put-object --bucket ukceh-fdri-staging-geospatial --key project=fdri/location_type=catchment/location=tweed/data_category=dsm/processing_level=processed/date=2026-03-20/clipped_tweed_dsm_3857_colourised_cog.tif --body /var/lib/localstack/data/clipped_tweed_dsm_3857_colourised_cog.tif
awslocal s3api put-object --bucket ukceh-fdri-staging-geospatial --key project=fdri/location_type=national/location=uk/data_category=soil_moisture/processing_level=processed/date=2026-03-20-2026-05-01/cosmos_sites.geojson --body /var/lib/localstack/data/cosmos_sites.geojson
