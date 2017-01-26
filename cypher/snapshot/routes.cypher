// Determines if a particular IP block is reachable from collectors
match (c:Collector), (b:IP_Block)
where b.block="8.0.0.0/8"
return c.name as Collector, b.block as IP_Block, exists( (c)<--(:Route)-->(b) ) as Reachable;

// Check which ASes are advertising the IP block
match (a:AS)-->(b:IP_Block)
where b.block="8.0.0.0/8"
return a.ASN as ASN, a.name as Name;

// Shortest route to IP block


