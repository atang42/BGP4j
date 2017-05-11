// Determines if a particular IP block is reachable from collectors
match (c:Collector), (b:IP_Block)
where b.block="8.0.0.0/8"
return c.name as Collector, b.block as IP_Block, exists( (c)-[*]->(b) ) as Reachable;

// Check which ASes are advertising the IP block
match (a:AS)-->(b:IP_Block)
where b.block="8.0.0.0/8"
return a.ASN as ASN, a.name as Name;

// Determine if a particular AS is reachable from collectors
match (c:Collector), (a:AS)
where a.ASN="3"
return c.name as Collector, a.ASN as ASN, a.name as AS_Name, exists( (c)-[:TO*]->(a) as Reachable;

// Determine prefixes advertised by multiple ASs
match(prefix:IP_Block)<-[:ORIGINATES]-(as:AS)
with prefix, collect(as) as AS_List
where size(AS_List) > 1
return prefix, AS_List
