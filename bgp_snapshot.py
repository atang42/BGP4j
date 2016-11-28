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

# open files for neo4j-import
collector_file = open("csv/collector.csv",'w')
ASN_file = open("csv/ASN.csv",'w')
prefix_file = open("csv/prefix.csv", 'w')
connections_file = open("csv/connections.csv",'w')

# formats for files
collector_file.write("collectorID:ID,name,:LABEL\n")
ASN_file.write("asnID:ID,ASN,:LABEL\n")
prefix_file.write("prefixID:ID,block,:LABEL\n")
connections_file.write(":START_ID,:END_ID,:TYPE,\n")

collector_file.write('{c},{c},Collector\n'.format(c=collector))
collector_file.close()

# keep track of which ones were already seen
ASN_set = set()
prefix_set = set()
connections_set = set()

# Main loop
while(stream.get_next_record(rec)):
  elem = rec.get_next_elem()
  while(elem):
    prefix  = elem.fields['prefix']
    as_path = elem.fields['as-path'].split(' ')
    communities = elem.fields['communities']
    print as_path
    
    # Connection from collector to peer
    if(not as_path[0] in ASN_set):
      ASN_set.add(as_path[0])
      ASN_file.write("{asn},{asn},AS\n".format(asn=as_path[0]))
    if(not (collector,as_path[0]) in connections_set):
      connections_set.add((collector,as_path[0]))
      connections_file.write("{c},{asn},CONNECTED\n".format(c=collector,asn=as_path[0]))

    for i in range(len(as_path)-1):
      # Connections along AS Path
      if(not as_path[i+1] in ASN_set):
        ASN_set.add(as_path[i+1])
        ASN_file.write("{asn},{asn},AS\n".format(asn=as_path[i+1]))
      if(not (as_path[i],as_path[i+1]) in connections_set):
        connections_set.add((as_path[i],as_path[i+1]))
        connections_file.write("{asn1},{asn2},CONNECTED\n".format(asn1=as_path[i],asn2=as_path[i+1]))


    # Connection to IP block
    if(not prefix in prefix_set):
      prefix_set.add(prefix)
      prefix_file.write("{pfx},{pfx},IP_BLOCK\n".format(pfx=prefix))
    if(not (as_path[-1],prefix) in connections_set):
      connections_set.add((as_path[-1],prefix))
      connections_file.write("{asn},{pfx},ORIGINATES\n".format(asn=as_path[-1],pfx=prefix))

    elem = rec.get_next_elem()
 
ASN_file.close()
prefix_file.close()
connections_file.close()
