// Determines if a particular IP block has a route from collectors at a time
match (c:Collector), (b:IP_Block), (t:Time)
where b.block = "208.65.153.0/24"
return t.time as Time, c.name as Collector, b.block as IP_Block, exists( (c)<--(:Route)-->(b)) as Reachable;

// Shows which peers to the collector advertised a route at each time
match (c:Collector)-[:TO]->(as:AS), (b:IP_Block), (t:Time)
where b.block = "208.65.153.0/24"
return t.time as Time, c.name as Collector, as.ASN as Peer_ASN, as.name as Peer_Name, exists( (as)<--(:Route)-->(b)) as Has_Route
order by Collector, Time, Peer_ASN;

// Check which ASes are advertising the IP block and the number of routes that go through there at each ime
match (a:AS)-->(b:IP_Block),
      (a)<--(r:Route)-->(b), 
      (t:Time)-->(r)
where b.block="208.65.153.0/24"
return t.time as Time, a.ASN as ASN, a.name as Name, b.block as IP_Block, count(r) as Num_Routes
order by Time, ASN, Num_Routes desc;

// Shortest routes to an IP Block from each collector at each time
match(c:Collector)<--(r:Route)-->(b:IP_Block), (t:Time)-->(r)
where b.block = "208.65.153.0/24"
with t, c, b, collect(r) as routes, min(r.length) as minLength
with t, c, b, filter(x in routes where x.length = minLength) as routes
match (c)<--(r:Route)-[rel:HAS_AS]->(as:AS) 
where r in routes
with t, c, b, r, as order by rel.order
with t, c, b, r, collect(as.ASN) as Route
return t.time as Time, c.name as Collector, b.block as IP_Block, r.length as Length, Route
order by Time, Collector, Length;

//Distribution of advertised route lengths to a single block
match (c:Collector)<--(r:Route)-->(b:IP_Block) 
where b.block = "208.65.153.0/24"
return c.name as Collector, r.length as Length, count(r) as Count
order by Collector, Length;


