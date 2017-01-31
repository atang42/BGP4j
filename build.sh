#!/bin/sh

# A script for importing all the csv files that get generated

# Change these to wherever the programs and targets are on your computer
IMPORT="/Users/alanmac/neo4j/bin/neo4j-import"
CSV_DIR="csv"
TARGET="/Users/alanmac/neo4j/data/databases/graph.db"

COMMAND="$IMPORT --delimiter | \
                 --into $TARGET \
                 --nodes $CSV_DIR/collector.csv
                 --nodes $CSV_DIR/AS.csv \
                 --nodes $CSV_DIR/prefix.csv \
                 --nodes $CSV_DIR/connections.csv \
                 --nodes $CSV_DIR/route.csv \
                 --relationships $CSV_DIR/connect_rels.csv \
                 --relationships $CSV_DIR/route_rels.csv"


# Make sure database is empty
rm -rf $TARGET/*

echo $COMMAND
$COMMAND
