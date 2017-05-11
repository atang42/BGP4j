// Determines if a particular IP block has a route from collectors
match (c:Collector), (b:IP_Block)
where b.block="8.0.0.0/8"
return c.name as Collector, b.block as IP_Block, exists( (c)<--(:Route)-->(b) ) as Reachable;

// Shows which peers to the collector advertised a route
match (c:Collector)-[:TO]->(as:AS), (b:IP_Block)
where b.block = "8.0.0.0/8"
return c.name as Collector, as.ASN as Peer_ASN, as.name as Peer_Name, exists( (as)<--(:Route)-->(b)) as Has_Route
order by Collector, Peer_ASN;

// Check which ASes are advertising the IP block and the number of routes that go through there
match (a:AS)-->(b:IP_Block),
      (a)<--(r:Route)-->(b)
where b.block="8.0.0.0/8"
return a.ASN as ASN, a.name as Name, b.block as IP_Block, count(r) as Num_Routes;
order by ASN, Num_Routes desc;

// Shortest routes to an IP Block from each collector
match(c:Collector)<--(r:Route)-->(b:IP_Block)
where b.block = "8.0.0.0/8"
with c, b, collect(r) as routes, min(r.length) as minLength
with c, b, filter(x in routes where x.length = minLength) as routes
match (c)<--(r:Route)-[rel:HAS_AS]->(as:AS) 
where r in routes
with c, b, r, as order by rel.order
with c, b, r, collect(as) as Route
return c.name as Collector, b.block as IP_Block, r.length as Length, Route
order by Collector, Length;

//Distribution of advertised route lengths to a single block
match (c:Collector)<--(r:Route)-->(b:IP_Block)
where b.block = "8.0.0.0/8"
return c.name as Collector, r.length as Length, count(r) as Count
order by Collector, Length;

// How many routes an AS appears in
match (as:AS)<-[:HAS_AS]-(r:Route)
return as.ASN as ASN, as.name as Name, count(r) as Num_Routes
order by Num_Routes desc

// How many routes to an ip address
match (ip:IP_Block)<-[:HAS_IP_BLOCK]-(r:Route)
return ip.block as IP_Block, count(r) as Num_Routes
order by Num_Routes desc

// Pairs that share routes
match (a:AS)<-[:HAS_AS]-(r:Route)-[:HAS_AS]->(b:AS)
return a, b, count(r) as Num_Routes
order by Num_Routes desc

// How many AS path prepending
match (r:Route)-[rel:HAS_AS]->()
where rel.order != r.length
return count(r)


