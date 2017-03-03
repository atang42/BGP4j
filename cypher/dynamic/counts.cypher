// Queries to count various node types

// Count AS
match (a:AS) return count(a) as ASes;

// Count Collectors
match (c:Collector) return count(c) as Collectors;

// Count IP Blocks
match (b:IP_Block) return count(b) as Blocks;

// Count Peers of Collectors
match (c:Collector)-[]-(a:AS) 
return c.name as Collector, count(a) as Peers;

// Count Timesteps
match (t:Time) return count (t) as Timesteps;

// Count Routes
match (r:Route) return count(r) as Routes;

