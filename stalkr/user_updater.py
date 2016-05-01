import os
from py2neo import Graph, Relationship, authenticate, Node
import crawler
import time

# set up neo4j
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
print('Connecting to Neo4j at {0}:{1}'.format(neodb, neoport))
authenticate(neodb + ':' + neoport, "neo4j", "1234")
graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

users = graph.cypher.execute("MATCH (u:User) WHERE u.followers_count IS NULL RETURN u")
user_count = graph.cypher.execute("MATCH (u:User) WHERE u.followers_count IS NULL RETURN count(u)")[0]["count(u)"]

print ">> Found {0} out of date user(s). Starting to update...".format(user_count)

ids = []
token = crawler.get_bearer()

def remove_users():
	print len(ids)
	for id in ids:
		print ">> User with id:{0} is no more. Deleting...".format(id)
		graph.cypher.execute("MATCH (u:User) WHERE u.id = {0} DETACH DELETE u".format(id))
	
for i in range(0, user_count, 1):
	ids.append(users[i]["u"]["id"])
	if i % 99 == 0 and not i == 0 or i == user_count - 1:
		done = False
		while not done:
			try:
				crawler.check_rates(token)
				data = crawler.get_users_data(ids, token)				

				if data is not None:
					if "errors" in data:
						remove_users()
						break

					for d in data:
						crawler.push_user(d)
					ids = []
					done = True
			except KeyboardInterrupt:
				sys.exit()
			except Exception:
				print ">> Exception! Proceeding to next chunk."
				time.sleep(10)
				pass
	

