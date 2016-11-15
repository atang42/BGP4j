#!/usr/bin/env python

from _pybgpstream import BGPStream, BGPRecord, BGPElem
from collections import defaultdict

stream = BGPStream()
rec = BGPRecord()

stream.add_filter('collector', 'rrc01')

stream.add_filter('record-type','ribs')

stream.add_interval_filter(1438415400,1438416600)

stream.add_filter('prefix', '8.8.8.0/24')

stream.start()

prefix_origin = defaultdict(set)

while(stream.get_next_record(rec)):
  #print "New Record"
  #print rec.status
  #print rec.time
  #print rec.dump_position
  #print
  elem = rec.get_next_elem()
  while(elem):
    print 'TYPE:' , elem.type
    print 'TIME:' , elem.time
    print 'PEER_ADDRESS:' , elem.peer_address
    print 'PEER_ASN:' , elem.peer_asn
    print 'FIELDS:' , elem.fields
    print
    elem = rec.get_next_elem()
   

