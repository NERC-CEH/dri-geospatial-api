from pathlib import Path
from unittest import mock

import pytest

from geospatial_api.utils import get_file_path, get_s3_client


class TestGetFilePath:
    def test_local_file_path(self, data_dir: Path) -> None:
        """Check a valid local file path is returned unmodified."""
        input_path = data_dir.joinpath("test_raster_3857_cog_rendered.tif")
        mock_s3_client = mock.MagicMock()
        file_path = get_file_path(url=input_path, s3_client=mock_s3_client)

        mock_s3_client.assert_not_called()
        assert file_path == str(input_path)

    def test_invalid_local_file_path(self, data_dir: Path) -> None:
        """Check a local file path raises an error if it does not exist."""
        input_path = data_dir.joinpath("test_raster.tif")

        with pytest.raises(FileExistsError, match=f"The provided path does not exist: {str(input_path)}"):
            get_file_path(url=input_path, s3_client=mock.MagicMock())

    def test_remote_formatted_local_file_path(self, data_dir: Path) -> None:
        """Check a local path in the format of `file:////path_to/raster.tif` is parsed correctly."""
        input_path = data_dir.joinpath("test_raster_3857_cog_rendered.tif")
        mock_s3_client = mock.MagicMock()
        file_path = get_file_path(url=f"file:///{input_path}", s3_client=mock_s3_client)

        mock_s3_client.assert_not_called()
        assert file_path == str(input_path)

    def test_s3_url(self) -> None:
        s3_url = "S3://ukceh-fdri-staging-geospatial/raster/test_raster_3857_cog_rendered.tif"

        mock_s3_client = mock.MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "presigned_s3"

        file_path = get_file_path(url=s3_url, s3_client=mock_s3_client)

        assert file_path == "presigned_s3"


class TestGetS3Client:
    def test_get_s3_client(self) -> None:
        """Check a boto3 client is returned from get_s3_client."""
        s3_client = get_s3_client()

        assert str(type(s3_client)) == "<class 'botocore.client.S3'>"
