import os
from py2neo import Graph, Relationship, authenticate, Node
import time
import topics
import math
import operator
import re

# set up neo4j
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
print('Connecting to Neo4j at {0}:{1}'.format(neodb, neoport))
authenticate(neodb + ':' + neoport, "neo4j", "1234")
graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

def tokenize(query):
	tokens = topics.get_topics(query)
	tokenized = {}
	for token in tokens:
		if token in tokenized:
			tokenized[token] += 1
		else:
			tokenized[token] = 1
	return tokenized

def tf_idf(query):
	scores = {}
	lengths = {}
	collection_size = graph.cypher.execute("MATCH (u:User) RETURN count(u)")[0]["count(u)"]

	# For each token in query
	for token, count in query.iteritems():
		print ">> Processing token: {0}".format(token)
		# Retrieve users who discuss this topic
		users = graph.cypher.execute("MATCH (u:User)-[:DISCUSSES]->(w:Word) WHERE w.name = \"{0}\" RETURN u.screen_name, u.terms, u.term_count".format(token))
		# Document frequency
		df = len(users)
		print ">> Found {0} users".format(df)
		# Query score
		wtq = count * math.log10(collection_size / df) * math.log10(collection_size / df)
		counter = 1
		for user in users:
			if counter % 100 == 0:
				print ">> Processed {0} users".format(counter)
			screen_name = user["u.screen_name"]
			terms = user["u.terms"]
			length = user["u.term_count"]
			# Term frequency for 'user'
			q = "{0}:".format(token)
			idx = terms.find(q)
			sub = terms[(idx + len(q)):]
			user_count = int(sub[:sub.find(" ")])				

			wtd = user_count
			if screen_name in scores:
				scores[screen_name] += wtq * wtd
			else:
				lengths[screen_name] = length
				scores[screen_name] = wtq * wtd
			counter += 1

	# Normalize scores by document size (user length)
	for user, score in scores.iteritems():
		# Normalize by square root of length
		scores[user] = score / math.sqrt(lengths[user])

	return scores

query = "donald trump"
result = tf_idf(tokenize(query))
sorted_x = sorted(result.items(), key = operator.itemgetter(1), reverse = True)
print sorted_x
