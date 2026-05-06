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

## Setup for local development

To develop the API locally both localstack and postgis docker containers need to be running. Localstack is used to 
create local AWS resources and PostGIS provides the database storing a list of available layers and their configurations

### Github configuration

The API and PostGIS database both require access to the private 
[dri-database-models](https://github.com/NERC-CEH/dri-database-models) repo. 
This means Git will need to be configured to be able to clone private repos over HTTPS.  
The easiest way to do this is with the [GitHub CLI](https://cli.github.com/):

```commandline
gh auth login
gh auth setup-git
```

Similarly, the Docker build needs to be able to clone the repo.
You'll need to create a GitHub [Personal Access Token][] and store it
in the `GH_TOKEN` environment variable ([direnv][] might be useful for
this).

[direnv]: https://direnv.net/
[Personal Access Token]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic

Example of adding GH personnal token to an environment variable, which will be picked up by Dockerfile in docker compose.

```commandline

cd dri-geospatial-api

sudo apt install direnv
eval "$(direnv hook bash)"  <-- add this to end of ~/.bashrc
echo export GH_TOKEN=my-personal-access-token > .envrc
direnv allow .
source ~/.bashrc
echo ${GH_TOKEN-nope}
```

### Docker compose

Once the github token has been configured, the localstack and PostGIS containers can be created using the following
docker compose command. 

```commandline
docker compose --profile localstack --profile db up
```

This will create or clear and reinitialise the database, including adding loading all test data and registering it with
the postgis database. 

## Adding / Deleting test data

### Localstack

When the localstack container is initialised, it runs the script `localstack-setup.sh`, found in `./bin`. 
This creates the buckets and loads the sample geospatial data located within `./data`. Each test data file is listed
separately, with the file expected to be located in `./data`

After `localstack-setup.sh` has been modified, it is recommended to clear the existing volumes and recreate them
to ensure that the modified test data is initialised correctly. To do this, the simplest way is to stop the docker 
compose session (ctrl + c, or `docker compose down -v`) before running the following

```commandline
docker system prune
docker volume rm $(docker volume ls -q)
```

### PostGIS

The initial database configuration and entries are controlled by `./bin/db-init/init.py`. To add a new entry corresponding
to an item in `./data`, the `initialise_db` function will need editing to add a new entry to the list of layers, ensuring
that any dependent tables (data categories etc) are also updated. 

Similar to editing localstack, to apply the changes, stop docker compose and clear all volumes before rebuilding
the containers to ensure the changes are picked up correctly.The `--build` option added to the docker compose command
ensures that new changes to the database models are applied.

```commandline
docker system prune
docker volume rm $(docker volume ls -q)
docker compose --profile localstack --profile db --build
```

#### Temporarily adding entries to the postgis database from external data

The API has a series of endpoints under the layer management router (`./src/geospatial_api/routers/layer_management.py)
which allow easy addition of new model entries for all sub-models and the main layer model.


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
