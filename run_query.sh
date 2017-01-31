

COMMAND="/Users/alanmac/neo4j/bin/neo4j-shell -c"
FILE=$1

echo "$COMMAND < $FILE"

$COMMAND < $FILE
