#!/bin/sh

#
# Setup script for a simple testing Postgres database.
#

psql -U postgres postgres << EOF
CREATE TABLE animals (name VARCHAR(100), color VARCHAR(100));
GRANT ALL PRIVILEGES ON animals TO postgres;

INSERT INTO animals (name, color) VALUES ('dog', 'brown');
INSERT INTO animals (name, color) VALUES ('cat', 'black');
EOF
