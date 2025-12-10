[![tests badge](https://github.com/NERC-CEH/dri-geospatial-api/actions/workflows/pipeline.yml/badge.svg)](https://github.com/NERC-CEH/dri-geospatial-api/actions)
[![docs badge](https://github.com/NERC-CEH/dri-geospatial-api/actions/workflows/deploy-docs.yml/badge.svg)](https://nerc-ceh.github.io/dri-geospatial-api/)

# Geospatial Data API

An API for accessing geospatial data

## Getting Started

## Virtual environment setup

This both creates the initial venv and also updates it

```commandline
uv sync
source .venv/bin/activate
```

## Linting

Linting uses ruff using the config in pyproject.toml

```
ruff check --fix
```

## Formatting

Formatting uses ruff using the config in pyproject.toml which follows the default black settings.

```
ruff format .
```

## Static type checking

Static type checking is undertaken using pyright using the config values in pyproject.toml

## Pre commit hooks

The linting, formatting and type checking can be called as a pre-commit hook. Run below to set them up.

```
pre-commit install
```

If you need to ignore the hook for a particular commit then use the `--no-verify` flag.

### Run the Tests

To run the tests, ensure the localstack docker container is running, and the virtual environment is activated. Then run:

```commandline
pytest
```
