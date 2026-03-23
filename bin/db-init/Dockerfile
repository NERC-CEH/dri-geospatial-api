FROM condaforge/miniforge3:25.11.0-0

RUN apt update && apt install -y --no-install-recommends git

# Copy the requirements file and install dependencies
COPY requirements.txt ./

RUN --mount=type=secret,id=GH_TOKEN,env=GH_TOKEN \
    git config --global url."https://x-access-token:$GH_TOKEN@github.com/".insteadOf https://github.com/ && \
    pip install --no-cache-dir -r requirements.txt

# Install psycopg2 dependency
# RUN apt update && apt install -y --no-install-recommends gcc musl-dev postgresql-dev
RUN apt update && apt install -y --no-install-recommends gcc musl-dev postgresql postgis

# Install gdal and rasterio via conda
RUN conda install rasterio

# Copy the initialization and db scripts into the container
COPY *.py ./

# # Copy the contents of the data directory so the layer registry can be built successfully
# RUN mkdir /data
# COPY ../data/* /data

# Set the entrypoint to run the Python script
ENTRYPOINT ["python", "init.py"]
