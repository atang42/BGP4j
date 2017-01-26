// Queries to count various node types

// Count AS
match (a:AS) return count(a) as ASes;

// Count Collectors
match (c:Collector) return count(c) as Collectors;

// Count IP Blocks
match (b:IP_Block) return count(b) as Blocks;

// Count Peers of Collectors
match (c:Collector)-->()-->(a:AS) return c as Collector, count(a) as Peers;

// Count Routes
match (c:Collector)<--(r:Route) return c as Collector,count(r) as Routes;

// Count Routes by peer
match (c:Collector)-->(conn:Connection)-->(peer:AS),
      (conn)<-[:HAS_CONNECTION]-(r:Route)
return c.name as Collector, peer.ASN as Peer_ASN, peer.name as Peer_Name, count(r) as Count
order by Collector, Count desc;

// Count Connections
match (c:Connection) return count(c) as Connections;
