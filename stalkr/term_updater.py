import os
from py2neo import Graph, Relationship, authenticate, Node
import sys
import time

# set up neo4j
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
print('Connecting to Neo4j at {0}:{1}'.format(neodb, neoport))
authenticate(neodb + ':' + neoport, "neo4j", "1234")
graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

graph.cypher.execute("CREATE CONSTRAINT ON (u:User) ASSERT u.id IS UNIQUE")
graph.cypher.execute("CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE")
graph.cypher.execute("CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE")
graph.cypher.execute("CREATE CONSTRAINT ON (w:Word) ASSERT w.name IS UNIQUE")

CHUNK_SIZE = 200
OFFSET = 800
# LIMIT = 22000
user_count = graph.cypher.execute("MATCH (u:User)-[:DISCUSSES]->() WHERE u.terms IS NULL RETURN count(DISTINCT u)")[0]["count(DISTINCT u)"]

# print ">> Offset:{0} / Limit:{1}".format(OFFSET, LIMIT)
print ">> Found {0} users. Starting processing...".format(user_count)

processed_users = 0
acum = 0

last_time = time.time()
for i in range(0, user_count, CHUNK_SIZE):	
	for uu in graph.cypher.execute("MATCH (u:User)-[:DISCUSSES]->() WHERE u.terms IS NULL RETURN DISTINCT u SKIP {0} LIMIT {1}".format(OFFSET, CHUNK_SIZE)):
		u = uu["u"] # user node object
		discussions = graph.cypher.execute("MATCH (u:User)-[d:DISCUSSES]->(w:Word) WHERE u.screen_name = \"{0}\" RETURN d, w".format(u["screen_name"]))
		terms = ""
		term_count = 0;
		for d in discussions:
			token = d["w"]["name"]
			count = d["d"]["count"]
			terms += "{0}:{1} ".format(token, count)
			term_count += count
		u["terms"] = terms
		u["term_count"] = term_count		
		processed_users += 1
		u.push()
	now = time.time()
	print ">> Processed {0} users. Loop time: {1}".format(processed_users, now - last_time)
	last_time = now
	
