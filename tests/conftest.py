from pathlib import Path

import pytest


@pytest.fixture
def data_dir() -> Path:
    data_dir = Path(__file__).parents[1].joinpath("data")
    return data_dir
