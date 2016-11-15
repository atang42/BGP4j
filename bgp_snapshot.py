#!/usr/bin/env python

# Collects snapshot data from a ribs file and adds those nodes and 
# connections to a database file

from _pybgpstream import BGPStream, BGPRecord, BGPElem
from collections import defaultdict

from neo4j.v1 import GraphDatabase, basic_auth

# Initialize BGPStream with relevant filters
stream = BGPStream()
rec = BGPRecord()

collector = 'rrc01'
stream.add_filter('collector', collector)
stream.add_filter('record-type','ribs')
stream.add_interval_filter(1438415400,1438416600)
stream.add_filter('prefix', '8.8.0.0/16')

stream.start()

# Connect to existing neo4j session 
driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "neo4j"))
session = driver.session()

session.run("MERGE (v:Collector {name:'" + collector + "'})")

# Main loop
while(stream.get_next_record(rec)):
  elem = rec.get_next_elem()
  while(elem):
    prefix  = elem.fields['prefix']
    as_path = elem.fields['as-path'].split(' ')
    communities = elem.fields['communities']
    print as_path
    
    # Connection from collector to peer
    session.run("MERGE (c:Collector {name:'" + collector + "'}) " + 
                "MERGE (as:AS {ASN:'" + as_path[0] + "'}) " + 
                "MERGE (c)-[:CONNECTED]->(as)")

    for i in range(len(as_path)-1):
      # Connections along AS Path
      session.run("MERGE (as1:AS {ASN:'" + as_path[i] + "'}) " + 
                  "MERGE (as2:AS {ASN:'" + as_path[i+1] + "'}) " + 
                  "MERGE (as1)-[:CONNECTED]->(as2)")

    # Connection to IP block
    session.run("MERGE (ip:IP_block {prefix:'" + prefix + "'}) " + 
                "MERGE (as:AS {ASN:'" + as_path[-1] + "'}) " + 
                "MERGE (as)-[:ORIGINATES]->(ip)")

    # Assign communities
    #for c in communities:
    #  session.run("MERGE (as:AS {{ASN:'{asn}'}}) ".format(asn=c['asn']) +
    #              "SET as.communities = coalesce(as.communities,[]) + {value}".format(value=c['value']))

    elem = rec.get_next_elem()
 
