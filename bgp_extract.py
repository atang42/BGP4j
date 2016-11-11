import re


def get_fields(fin):
    tags = []
    tag_re = re.compile("(\w+):?")
    i = 0
    for line in fin:
        result = tag_re.match(line)

        if result == None:
            continue
    
        tag = result.group(1)
        if not tag in tags:
            tags.append(tag)

        i += 1
        if i % 1000000 == 0:
            print i, tags
            
    return tags

tags = ['TIME', 'TYPE', 'PREFIX', 'SEQUENCE',
        'FROM', 'ORIGINATED', 'ORIGIN', 'ASPATH',
        'NEXT_HOP', 'COMMUNITY', 'MULTI_EXIT_DISC',
        'ATOMIC_AGGREGATE', 'AGGREGATOR', 'MP_REACH_NLRI']

class RoutingEntry:
    def __init__(self):
        self.time             = ""
        self.type             = ""
        self.prefix           = ""
        self.sequence         = ""
        self.sent_from        = ("","")
        self.sent_time        = ""
        self.origin           = ""
        self.as_path          = []
        self.next_nop         = []
        self.community        = []
        self.multi_exit_disc  = None
        self.atomic_aggregate = None
        self.aggregator       = ("","")
        self.mp_reach_nlri    = ""



    
        
