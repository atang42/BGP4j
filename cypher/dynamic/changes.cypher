// List the added routes
match(t1:Time) -[:NEXT]->(t2:Time), (t2)-[:CONNECTED]->(r:Route)
where not(exists( (t1)-[:CONNECTED]->(r)))
with t2 as t, r
match (r) -[rel:HAS_AS]->(as:AS)
with t, r, as order by rel.order
with t, r, collect(as.ASN) as Added_Route
match (r) -[:HAS_IP_BLOCK]->(ip:IP_Block)
return t.time as Time, Added_Route, ip.block as Address
order by Time, Address;


// List removed routes
match(t1:Time) -[:NEXT]->(t2:Time), (t1)-[:CONNECTED]->(r:Route)
where not(exists( (t2)-[:CONNECTED]->(r)))
with t2 as t, r
match (r) -[rel:HAS_AS]->(as:AS)
with t, r, as order by rel.order
with t, r, collect(as.ASN) as Removed_Route
match (r) -[:HAS_IP_BLOCK]->(ip:IP_Block)
return t.time as Time, Removed_Route, ip.block as Address
order by Time, Address;

// Counts of added and removed routes
match(t1:Time) -[:NEXT]->(t2:Time)
optional match (t1)-[:CONNECTED]->(r:Route)
where not(exists( (t2)-[:CONNECTED]->(r)))
with t2, count(r) as Num_Removed

match(t1:Time) -[:NEXT]->(t2)
optional match (t2)-[:CONNECTED]->(r:Route)
where not(exists( (t1)-[:CONNECTED]->(r)))
with t2.time as Time, count(r) as Num_Added, Num_Removed

where (Num_Added <> 0 or Num_Removed <> 0)
return Time, Num_Added, Num_Removed;

// Route Changes
match(t1:Time) -[:NEXT]->(t2:Time), 
(t1)-[:CONNECTED]->(r1:Route),
(t2)-[:CONNECTED]->(r2:Route),
(r1)-[:HAS_AS {order:"1"}]-> (as:AS) <-[:HAS_AS {order:"1"}]- (r2), 
(r1)-[:HAS_IP_BLOCK]-> (ip:IP_Block) <-[:HAS_IP_BLOCK]- (r2)
with t2 as t, r1, r2, ip

match (r1) -[rel:HAS_AS]->(as:AS)
with t, r1, r2, ip, as order by rel.order
with t, r1, r2, ip, collect(as.ASN) as Old_Route

match (r2) -[rel:HAS_AS]->(as:AS)
with t, r1, r2, ip, Old_Route, as order by rel.order
with t, r1, r2, ip, Old_Route, collect(as.ASN) as New_Route
return t.time as Time, Old_Route, New_Route, ip.block as Address

order by Time, Address;



