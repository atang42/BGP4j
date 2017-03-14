// Various metrics of the graph

//AS with the most IP_Blocks
match (a:AS)-[:ORIGINATES]->(b:IP_Block)
return a.ASN as ASN, a.name as Name, count(b) as Num_Blocks 
order by count(b) desc
limit 30;

//Distribution of IP Block advertisements
match (a:AS)
optional match (a)-[:ORIGINATES]-(b:IP_Block)
with a as AS, count(b) as Num_Blocks
return Num_Blocks, count(AS) as Count
order by Num_Blocks;

//AS with most connections to other ASes
match (a:AS)-[:TO]-(b:AS)
return a.ASN as ASN, a.name as Name, count(b) as Num_ASes
order by count(b) desc
limit 30;

//Distribution of connections to other ASes
match (a:AS)-[:TO]-(b:AS)
with a as AS, count(b) as Num_ASes
return Num_ASes, count(AS) as Count 
order by Num_ASes;

//Average degree with other ASes
match (a:AS)-[:TO]-(b:AS)
with a.ASN as ASN, count(b) as Num_ASes
return avg(Num_ASes) as Average_Degree;

//Longest paths from collector to IP block
//match (a:Collector), (b:IP_Block), path = shortestPath( (a)-[*]->(b))
//return a.name as Collector, b.block as IP_Block, length(path)-1 as Length, nodes(path) as Path
//order by length(path) desc, IP_Block
//limit 20;

//Distribution of distance of address blocks from collectors
//match (a:Collector), (b:IP_Block), path = shortestPath( (a)-[*]->(b))
//with a.name as Collector, b as IP_Block, length(path)-1 as Length
//return Collector, Length, count(IP_Block) as Count 
//order by Collector, Length;

//Distribution of distance of ASes from collectors
match (a:Collector), (b:AS), path = shortestPath( (a)-[*]->(b))
with a.name as Collector, b, length(path)-1 as Length
return Collector, Length, count(b) as Count 
order by Collector, Length;

// In-degree vs out-degree of each AS
match (a:AS)
optional match (a)-[:TO]->(out:AS)
with a, count(out) as out_degree
optional match (a)<-[:TO]-(in:AS)
return a as AS, in_degree, count(in) as out_degree
order by in_degree - out_degree desc
limit 30;

// Show number of times a connection appears in the routing
match (a:AS)-[r:TO]->(b:AS)
return a, b, r.count order by r.count desc
limit 100;

// Local clustering coefficient of each AS
match (node:AS)-[:TO]-(neighbor:AS)
with node, count(neighbor) as degree
match (n1:AS)-[:TO]-(node)-[:TO]-(n2:AS)-[r:TO]-(n1)
with node, degree, count(r)/2 as edges
return node, toFloat(edges) / (degree * (degree-1) / 2) as clustering
order by clustering desc limit 100;

// Page rank using APOC
MATCH (node:AS)
WITH collect(node) AS nodes
CALL apoc.algo.pageRank(nodes) YIELD node, score
RETURN node, score
ORDER BY score DESC
limit 100;

// Incoming Closeness using APOC - measure distance from other nodes
match (node:AS)
WITH collect(node) AS nodes
CALL apoc.algo.closeness(['TO'],nodes,'INCOMING') YIELD node, score
RETURN node, score
ORDER BY score DESC
limit 100;

// Incoming Betweenness using APOC
match (node:AS)
WITH collect(node) AS nodes
CALL apoc.algo.betweenness(['TO'],nodes,'INCOMING') YIELD node, score
RETURN node, score
ORDER BY score DESC
limit 100;
