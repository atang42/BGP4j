#!/usr/bin/env python

# Collects snapshot data from a ribs file and adds those nodes and 
# connections to a database file

from _pybgpstream import BGPStream, BGPRecord, BGPElem
from collections import defaultdict
import string

# Initialize BGPStream with relevant filters
stream = BGPStream()
rec = BGPRecord()

collectors = ['rrc01','rrc14','rrc15']
for collector in collectors:
  stream.add_filter('collector', collector)
stream.add_filter('record-type','ribs')
stream.add_interval_filter(1438415400,1438416600)
stream.add_filter('prefix', '8.0.0.0/8')

stream.start()


# open files for neo4j-import
collector_file = open("csv/collector.csv",'w')
AS_file = open("csv/AS.csv",'w')
prefix_file = open("csv/prefix.csv", 'w')
route_file = open("csv/route.csv", 'w')
connections_file = open("csv/connections.csv",'w')
connect_rels_file = open("csv/connect_rels.csv",'w')
route_rels_file = open("csv/route_rels.csv", 'w')

# formats for files
collector_file.write("name:ID|:LABEL\n")
AS_file.write("ASN:ID|name|:LABEL\n")
prefix_file.write("block:ID|:LABEL\n")
route_file.write(":ID|length:int|:LABEL\n")
connections_file.write(":ID|:LABEL\n")
connect_rels_file.write(":START_ID|:END_ID|:TYPE|\n")
route_rels_file.write(":START_ID|:END_ID|:TYPE|\n")

for collector in collectors:
  collector_file.write('{c}|Collector\n'.format(c=collector))
collector_file.close()

# keep track of which ones were already seen
AS_set = set()
prefix_set = set()
connections_set = set()
route_set = set()

# Main loop
route_id = None
while(stream.get_next_record(rec)):
  elem = rec.get_next_elem()
  collector = rec.collector
  while(elem):
    prefix  = elem.fields['prefix']
    as_path = elem.fields['as-path'].split(' ')
    print as_path

    route_id = (collector, as_path[0], prefix)

    # Skip duplicate routes
    if route_id in route_set:
      elem = rec.get_next_elem()
      continue

    route_set.add(route_id)
    route_file.write("{rid}|{length}|Route\n".format(rid=route_id,length=len(as_path)))
    route_rels_file.write("{rid}|{c}|HAS_COLLECTOR\n".format(rid=route_id,c=collector))
    route_rels_file.write("{rid}|{p}|HAS_IP_BLOCK\n".format(rid=route_id,p=prefix))
    
    # Connection from collector to peer
    if(not as_path[0] in AS_set):
      AS_set.add(as_path[0])

    pair = (collector,as_path[0])
    if(not pair in connections_set):
      connections_set.add(pair)
      connections_file.write("{p}|Connection\n".format(p=pair))
      connect_rels_file.write("{c}|{p}|FROM\n".format(p=pair,c=collector))
      connect_rels_file.write("{p}|{asn}|TO\n".format(p=pair,asn=as_path[0]))
    route_rels_file.write("{rid}|{asn}|HAS_AS\n".format(rid=route_id,asn=as_path[0]))
    route_rels_file.write("{rid}|{conn}|HAS_CONNECTION\n".format(rid=route_id,conn=pair))

    for i in range(len(as_path)-1):
      # Skip AS path prepending
      if as_path[i+1] == as_path[i]:
        continue
      
      # Connections along AS Path
      if(not as_path[i+1] in AS_set):
        AS_set.add(as_path[i+1])
      pair = (as_path[i],as_path[i+1])
      if(not pair in connections_set):
        connections_set.add(pair)
        connections_file.write("{p}|Connection\n".format(p=pair))
        connect_rels_file.write("{asn}|{p}|FROM\n".format(p=pair,asn=as_path[i]))
        connect_rels_file.write("{p}|{asn}|TO\n".format(p=pair,asn=as_path[i+1]))

      route_rels_file.write("{rid}|{asn}|HAS_AS\n".format(rid=route_id,asn=as_path[i+1]))
      route_rels_file.write("{rid}|{conn}|HAS_CONNECTION\n".format(rid=route_id,conn=pair))

    # Connection to IP block
    if(not prefix in prefix_set):
      prefix_set.add(prefix)
      prefix_file.write("{pfx}|IP_Block\n".format(pfx=prefix))
    if(not (as_path[-1],prefix) in connections_set):
      connections_set.add((as_path[-1],prefix))
      connect_rels_file.write("{asn}|{pfx}|ORIGINATES\n".format(asn=as_path[-1],pfx=prefix))

    elem = rec.get_next_elem()

# Output ASN and AS Names
asnames_file = open("asnames.txt")
for line in asnames_file:
  l = line.split(None, 1)
  asn = l[0].lstrip(string.ascii_letters)
  name = l[1].rstrip()
  if asn in AS_set:
    AS_file.write("{asn}|{name}|AS\n".format(asn = asn, name = name))
    AS_set.remove(asn)

for asn in AS_set:
  AS_file.write("{asn}||AS\n".format(asn=asn))

AS_file.close()
prefix_file.close()
connections_file.close()
route_file.close()
connect_rels_file.close()
route_rels_file.close()
