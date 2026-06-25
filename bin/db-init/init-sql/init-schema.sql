
/*
  This script initializes the geospatial schema inside the fdri database.

  It is assumed it is running in the fdri database, which is specified by the POSTGRES_DB environment variable

  SQLAlchemy will populate it with the orm models from https://github.com/NERC-CEH/dri-database-models

*/
CREATE SCHEMA IF NOT EXISTS geospatial;
CREATE EXTENSION postgis;
