#!/bin/bash

docker run --detach --rm --name website-scraper -p 26257:26257 -p 8080:8080 cockroachdb/cockroach:v20.1.3 start-single-node --insecure --advertise-addr=localhost
sleep 5
psql 'postgresql://root@localhost:26257/scraper?sslmode=disable' -c 'CREATE DATABASE scraper'
psql 'postgresql://root@localhost:26257/scraper?sslmode=disable' < dbschema/schema.sql
psql 'postgresql://root@localhost:26257/scraper?sslmode=disable'
