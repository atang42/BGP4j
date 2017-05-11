#!/usr/bin/env python

# Models the links between ASes that can be inferred from the routing data

from _pybgpstream import BGPStream, BGPRecord, BGPElem
from collections import defaultdict
import string
import sys

# Separate string prefix into an
# int representation of bits and a mask length
def prefix_split(prefix):
  # Skip IPv6
  if(":" in prefix):
    return None

  (pref, mask) = prefix.split('/')
  bits = pref.split('.')

  result = 0
  for i in range(4):
    result <<= 8
    result += int(bits[i])

  return (result, int(mask))

# Write int and mask as string prefix
def write_prefix(result, mask):

  s = ""
  for i in range(3):
    s = '.' + str(result % 256) + s
    result >>= 8
  s = str(result % 256) + s

  return s + '/' + str(mask)

# Initialize BGPStream with relevant filters
stream = BGPStream()
rec = BGPRecord()

mode = ""
if len(sys.argv) == 1:
  collectors = ['rrc00', 'rrc01', 'rrc03', 'rrc04', 'rrc05']
  for collector in collectors:
    stream.add_filter('collector', collector)
  stream.add_filter('record-type','ribs')
  stream.add_interval_filter(1475310000,1475350000)
  stream.add_filter('prefix', '8.0.0.0/8')
  mode = 'ripe'
elif len(sys.argv) >= 2:
  filename = sys.argv[1]
  stream.set_data_interface('singlefile')
  stream.set_data_interface_option('singlefile', 'rib-file', filename)
  collectors = ['singlefile_ds']
  mode = 'file'

  if(len(sys.argv) >= 3):
    stream.add_filter('prefix', sys.argv[2])

stream.start()


# open files for neo4j-import
collector_file = open("csv/collector.csv",'w')
AS_file = open("csv/AS.csv",'w')
prefix_file = open("csv/prefix.csv", 'w')
route_file = open("csv/route.csv", 'w')
connections_file = open("csv/connections.csv",'w')
connect_rels_file = open("csv/connect_rels.csv",'w')
route_rels_file = open("csv/route_rels.csv", 'w')
subnet_rels_file = open("csv/subnet_rels.csv", 'w')

# formats for files
collector_file.write("name:ID|:LABEL\n")
AS_file.write("ASN:ID|name|:LABEL\n")
prefix_file.write("block:ID|size:int|:LABEL\n")
route_file.write(":ID|length:int|:LABEL\n")
connections_file.write(":ID|:LABEL\n")
connect_rels_file.write(":START_ID|:END_ID|:TYPE|\n")
route_rels_file.write(":START_ID|:END_ID|:TYPE|\n")
subnet_rels_file.write(":START_ID|:END_ID|:TYPE|\n")

for collector in collectors:
  collector_file.write('{c}|Collector\n'.format(c=collector))
collector_file.close()

# keep track of which ones were already seen
AS_set = set()
prefix_set = set()
connections_set = set()
route_set = set()

connections_count = dict()

# Main loop
route_id = None
while(stream.get_next_record(rec)):
  elem = rec.get_next_elem()
  collector = rec.collector
  while(elem):
    prefix  = elem.fields['prefix']
    as_path = elem.fields['as-path'].split(' ')

    # Skip duplicate routes
    if route_id in route_set:
      elem = rec.get_next_elem()
      continue
   
    # Connection from collector to peer
    if(not as_path[0] in AS_set):
      AS_set.add(as_path[0])

    if as_path[0] == '':
      elem = rec.get_next_elem()
      continue

    pair = (collector,as_path[0])
    if(not pair in connections_set):
      connections_set.add(pair)
      connect_rels_file.write("{c}|{asn}|VIEWS\n".format(c=collector,asn=as_path[0]))
      

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
        connections_count[pair] = 0
        # connect_rels_file.write("{asn1}|{asn2}|TO\n".format(asn1=as_path[i],asn2=as_path[i+1]))
      connections_count[pair] += 1

    # Connection to IP block
    if(not (prefix in prefix_set)):
      prefix_set.add(prefix)
      prefix_size = prefix.split('/')[1]
      prefix_file.write("{pfx}|{size}|IP_Block\n".format(pfx=prefix, size=prefix_size))
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
  name = name.replace('"', '\\"')
  if asn in AS_set:
    AS_file.write('{asn}|"{name}"|AS\n'.format(asn = asn, name = name))
    AS_set.remove(asn)

for asn in AS_set:
  AS_file.write("{asn}||AS\n".format(asn=asn))

# Output Subnet relationships
def calculate_subnets():
  split_pref = [prefix_split(p) for p in prefix_set]
  for p in prefix_set:
    if ":" not in p:
      split_pref.append(prefix_split(p))
  split_pref.sort(lambda x,y: x[0]-y[0] or x[1] - y[1])
  prefixes = [write_prefix(split_pref[a][0], split_pref[a][1]) for a in range(len(split_pref))]
  for a in range(len(split_pref)):
    for b in range(a+1, len(split_pref)):
      if ((split_pref[a][0] & split_pref[b][0]) == split_pref[a][0]):
        subnet_rels_file.write("{B}|{A}|SUBNET_OF\n".format(A = prefixes[a], B = prefixes[b]))
      else:
        break

# calculate_subnets()

# Output connections with count
for pair in connections_count:
  connect_rels_file.write("{asn1}|{asn2}|TO\n".format(asn1=pair[0],asn2=pair[1], ))


AS_file.close()
prefix_file.close()
connections_file.close()
route_file.close()
connect_rels_file.close()
route_rels_file.close()
