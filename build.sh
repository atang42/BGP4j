#!/bin/sh

IMPORT="/Users/alanmac/neo4j/bin/neo4j-import"
CSV_DIR="csv"
TARGET="/Users/alanmac/neo4j/data/databases/graph.db"

COMMAND="$IMPORT --into $TARGET \
                 --nodes $CSV_DIR/collector.csv \
                 --nodes $CSV_DIR/ASN.csv \
                 --nodes $CSV_DIR/prefix.csv \
                 --relationships $CSV_DIR/connections.csv"

# Make sure database is empty
rm -rf $TARGET/*

echo $COMMAND
$COMMAND
