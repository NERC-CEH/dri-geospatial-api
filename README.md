[![tests badge](https://github.com/NERC-CEH/dri-geospatial-api/actions/workflows/pipeline.yml/badge.svg)](https://github.com/NERC-CEH/dri-geospatial-api/actions)
[![docs badge](https://github.com/NERC-CEH/dri-geospatial-api/actions/workflows/deploy-docs.yml/badge.svg)](https://nerc-ceh.github.io/dri-geospatial-api/)

# Geospatial Data API

An API for accessing geospatial data

## Getting Started

### Virtual environment setup

To create the initial venv or update it:

```commandline
uv sync
```

To activate the venv:

```commandline
source .venv/bin/activate
```

To update the uv lock file (e.g. when adding a new dependency):

```commandline
uv lock
```

### Linting

Linting uses ruff using the config in pyproject.toml

```
ruff check --fix
```

### Formatting

Formatting uses ruff using the config in pyproject.toml which follows the default black settings.

```
ruff format .
```

### Static type checking

Static type checking is undertaken using pyright using the config values in pyproject.toml

### Pre commit hooks

The linting, formatting and type checking can be called as a pre-commit hook. Run below to set them up.

```
pre-commit install
```

If you need to ignore the hook for a particular commit then use the `--no-verify` flag.

## Run the Tests

To run the tests, ensure the localstack docker container is running, and the virtual environment is activated. Then run:

```commandline
pytest
```

## Localstack setup

Localstack is used to create local AWS resoruces for testing the app locally. `localstack-setup.sh` is run when the
container is initialised which creates the buckets and loads the sample geospatial data found in `./data`. If the contents of `./data` are updated then the localstack docker container will need to be stopped, the volume deleted and then recreated to pick up any new changes.

To run localstack:

```commandline
docker compose --profile localstack up
```


## Running the API locally.

The API can be run either within a python shell with the venv activated using `python -m geospatial_api`, or via a debug session. The configuration to use within a VSCode launch.json file for debugging the API is shown below.

```
{
    "name": "Run geospatial_api",
    "type": "debugpy",
    "request": "launch",
    "module": "geospatial_api",
    "justMyCode": false,
}
```

### URLs

Once running locally, documentation for the API can be found at http://localhost:8000/api/docs
