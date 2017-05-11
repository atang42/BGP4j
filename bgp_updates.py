#!/usr/bin/env python

# Collects data from ribs files and adds those nodes and 
# connections to a database file along with a node representing
# the time

from _pybgpstream import BGPStream, BGPRecord, BGPElem
from collections import defaultdict
import string
import datetime
import sys, os

# Timestep between Frame nodes
delta_time = 300

# Initialize BGPStream with relevant filters
stream = BGPStream()
rec = BGPRecord()

mode = ""
if len(sys.argv) == 1:
  collectors = ['rrc01']
  for collector in collectors:
    stream.add_filter('collector', collector)
  stream.add_filter('record-type', 'ribs')
  stream.add_filter('record-type', 'updates')
  stream.add_interval_filter(1203850000,1203920000)
  stream.add_rib_period_filter(70000)
  stream.add_filter('prefix', '208.65.153.0/22')
  mode = 'ripe'
elif len(sys.argv) == 2:
  dirname = sys.argv[1]
  filelist = os.listdir(dirname)
  filelist.sort()
  filelist = [dirname + os.sep + f for f in filelist]
  stream.set_data_interface('singlefile')
  stream.set_data_interface_option('singlefile','rib-file', filelist[0])
  # stream.add_filter('prefix', '8.8.0.0/16')
  filelist = filelist[1:]
  collectors = ['singlefile_ds']
  mode = 'file'

stream.start()


# open files for neo4j-import
collector_file = open("csv/collector.csv",'w')
AS_file = open("csv/AS.csv",'w')
prefix_file = open("csv/prefix.csv", 'w')
route_file = open("csv/route.csv", 'w')
time_file = open("csv/time.csv", 'w')
connect_rels_file = open("csv/connect_rels.csv",'w')
route_rels_file = open("csv/route_rels.csv", 'w')
time_rels_file = open("csv/time_rels.csv", 'w')

# formats for files
collector_file.write("name:ID|:LABEL\n")
AS_file.write("ASN:ID|name|:LABEL\n")
prefix_file.write("block:ID|:LABEL\n")
route_file.write(":ID|length:int|:LABEL\n")
time_file.write(":ID|time:int|year:int|month:int|day:int|hour:int|minute:int|second:int|:LABEL\n")
connect_rels_file.write(":START_ID|:END_ID|:TYPE|\n")
route_rels_file.write(":START_ID|:END_ID|:TYPE|order\n")
time_rels_file.write(":START_ID|:END_ID|:TYPE\n")

for collector in collectors:
  collector_file.write('{c}|Collector\n'.format(c=collector))
collector_file.close()

# keep track of which ones were already seen
AS_set = set()
prefix_set = set()
connections_set = set()
route_set = set()
curr_route_dict = dict()

# Add nodes to the neo4j database if they haven't yet been added 
def add_path(route_id, as_path):
  
  collector = route_id[0]
  prefix = route_id[2]

  # Create route
  route_file.write("{rid}|{length}|Route\n".format(rid=route_id,length=len(as_path)))
  route_rels_file.write("{rid}|{c}|HAS_COLLECTOR|null\n".format(rid=route_id,c=collector))
  route_rels_file.write("{rid}|{p}|HAS_IP_BLOCK|null\n".format(rid=route_id,p=prefix))
  route_set.add(route_id)

  # Connection from collector to peer
  if(not as_path[0] in AS_set):
    AS_set.add(as_path[0])

  pair = (collector,as_path[0])
  if(not pair in connections_set):
    connections_set.add(pair)
    connect_rels_file.write("{c}|{asn}|VIEWS\n".format(c=collector,asn=as_path[0]))
  route_rels_file.write("{rid}|{asn}|HAS_AS|1\n".format(rid=route_id,asn=as_path[0]))

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
      connect_rels_file.write("{asn1}|{asn2}|TO\n".format(asn1=as_path[i],asn2=as_path[i+1]))

    route_rels_file.write("{rid}|{asn}|HAS_AS|{order}`\n".format(rid=route_id,asn=as_path[i+1],order=i+2))

  # Connection to IP block
  if(not prefix in prefix_set):
    prefix_set.add(prefix)
    prefix_file.write("{pfx}|IP_Block\n".format(pfx=prefix))
  if(not (as_path[-1],prefix) in connections_set):
    connections_set.add((as_path[-1],prefix))
    connect_rels_file.write("{asn}|{pfx}|ORIGINATES\n".format(asn=as_path[-1],pfx=prefix))

# Handling ribs records
def handle_ribs(rec,timestep):
  elem = rec.get_next_elem()
  collector = rec.collector
  while(elem):
    prefix  = elem.fields['prefix']
    as_path = elem.fields['as-path'].split(' ')

    if as_path[0] == '':
      elem = rec.get_next_elem()
      continue

    route_id = (collector, as_path[0], prefix, elem.fields['as-path'])
    
    # Skip duplicate routes
    if route_id in route_set:
      elem = rec.get_next_elem()
      continue
    time_rels_file.write("{time}|{rid}|CONNECTED\n".format(time=timestep, rid=route_id))

    curr_route_dict[route_id[0:3]] = elem.fields['as-path']

    add_path(route_id, as_path)
    elem = rec.get_next_elem()

# Handle update records
def handle_updates(rec):
  elem = rec.get_next_elem()
  collector = rec.collector
  while(elem):
    # skip status messages
    if(elem.type == 'S'):
      elem = rec.get_next_elem()
      continue

    peer = elem.peer_asn
    prefix  = elem.fields['prefix']

    # Withdraw
    if(elem.type == 'W'):
      rid = (collector, peer, prefix) 
      if(rid in curr_route_dict):
        del curr_route_dict[rid]
    # Announce
    elif(elem.type == 'A'):
      route_id = (collector, peer, prefix, elem.fields['as-path'])
      if(route_id not in route_set):
        add_path(route_id, elem.fields['as-path'].split(' '))
      if(route_id[0:3] in curr_route_dict):
        print route_id, curr_route_dict[route_id[0:3]]
      curr_route_dict[route_id[0:3]] = elem.fields['as-path']
      print elem.fields['as-path']

    elem = rec.get_next_elem()
       
# Main handling loop
route_id = None
last_time = 0
last_print = 0
def process_records():
  global route_id
  global last_time
  global last_print
  CUTOFF = 60
  while(stream.get_next_record(rec)):

    if(rec.time > last_print):
        print rec.type, rec.dump_time, rec.time
        last_print = rec.time

    if rec.type=='rib':
      if(rec.time - last_time > CUTOFF):
        dt = datetime.datetime.fromtimestamp(rec.time)
        time_file.write("{time}|{time}|{Y}|{M}|{D}|{h}|{m}|{s}|Frame\n"
          .format(time=rec.time, 
                  Y=dt.year, M=dt.month, D=dt.day,
                  h=dt.hour, m=dt.minute, s=dt.second))
        last_time = rec.time
      handle_ribs(rec,last_time)

    if rec.type=='update' and last_time != 0:
      dt = datetime.datetime.fromtimestamp(last_time+delta_time)
      while(rec.time > last_time + delta_time):
        time_file.write("{time}|{time}|{Y}|{M}|{D}|{h}|{m}|{s}|Frame\n"
          .format(time=last_time+delta_time, 
                  Y=dt.year, M=dt.month, D=dt.day,
                  h=dt.hour, m=dt.minute, s=dt.second))
        time_rels_file.write("{t1}|{t2}|NEXT_FRAME\n".format(t1=last_time, t2=last_time+delta_time))

        for routes in curr_route_dict: 
          route_id = routes + (curr_route_dict[routes],)
          time_rels_file.write("{time}|{rid}|AVAILABLE\n".format(time=last_time+delta_time, rid=route_id))
        
        last_time += delta_time
   
      handle_updates(rec)

if(mode == 'ripe'):
  process_records()
elif(mode == 'file'):
  while len(filelist) > 0:
    process_records()
    print "next file", filelist[0]
    stream = BGPStream()
    stream.set_data_interface('singlefile')
    stream.set_data_interface_option('singlefile','upd-file', filelist[0])
    # stream.add_filter('prefix', '8.8.0.0/16')
    stream.start()
    filelist = filelist[1:]
  process_records()

  
# Output ASN and AS Names
asnames_file = open("asnames.txt")
for line in asnames_file:
  l = line.split(None, 1)
  asn = l[0].lstrip(string.ascii_letters)
  name = l[1].rstrip()
  name = name.replace('|', '')
  if asn in AS_set:
    AS_file.write("{asn}|{name}|AS\n".format(asn = asn, name = name))
    AS_set.remove(asn)

for asn in AS_set:
  AS_file.write("{asn}||AS\n".format(asn=asn))

AS_file.close()
prefix_file.close()
route_file.close()
connect_rels_file.close()
route_rels_file.close()
