// Various metrics of the graph

//AS with the most IP_Blocks
match (a:AS)-[:ORIGINATES]->(b:IP_Block)
return a.ASN as ASN, a.name as Name, count(b) as Num_Blocks 
order by count(b) desc
limit 10;

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
limit 10;

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
match (a:Collector), (b:IP_Block), path = shortestPath( (a)-[*]-(b))
return a.name as Collector, b.block as IP_Block, length(path)-1 as Length, nodes(path) as Path
order by length(path) desc, IP_Block
limit 10;

//Distribution of distance from collectors
match (a:Collector), (b:IP_Block), path = shortestPath( (a)-[*]-(b))
with a.name as Collector, b as IP_Block, length(path)-1 as Length
return Collector, Length, count(IP_Block) as Count 
order by Collector, Length;

//Average distance from collectors
match (a:Collector), (b:IP_Block), path = shortestPath( (a)-[*]-(b))
with a.name as Collector, b as IP_Block, length(path) as Length
return Collector, avg(Length) as Average_Length;
