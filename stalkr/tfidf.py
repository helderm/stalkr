import os
from py2neo import Graph, Relationship, authenticate, Node
import time
import topics
import math
import operator
import re
import numpy as np

# set up neo4j
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', '127.0.0.1')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
print('Connecting to Neo4j at {0}:{1}'.format(neodb, neoport))
authenticate(neodb + ':' + neoport, "neo4j", "neo4j")
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

def recommend(query, alpha = 0.5, pr_type = 'rankb', limit=30):

    query = tokenize(query)
    ret = []
    users = {}
    p_scores = {}

    lengths = {}
    collection_size = graph.cypher.execute("MATCH (u:User) RETURN count(u)")[0]["count(u)"]

    avgkey = 'avg(u.{0})'.format(pr_type)
    stdevkey = 'stdev(u.{0})'.format(pr_type)
    pravg = graph.cypher.execute('MATCH (u:User) RETURN {0}'.format(avgkey))[0][avgkey]
    prstdev = graph.cypher.execute('MATCH (u:User) RETURN {0}'.format(stdevkey))[0][stdevkey]

    i = 0
    # For each token in query
    for token, count in query.iteritems():
        #print ">> Processing token: {0}".format(token)
        # Retrieve users who discuss this topic
        cur = graph.cypher.execute("MATCH (u:User)-[d:DISCUSSES]->(w:Word) WHERE w.name = \"{0}\" RETURN u"
                                     ".id, u.screen_name, u.term_count, u.friends_count, u.followers_count, d.count, u.{1}".format(token, pr_type))
        # Document frequency
        df = len(cur)
        #print ">> Found {0} users".format(df)
        # Query score
        print collection_size, df
        wtq = count * math.log10(collection_size / df) * math.log10(collection_size / df)
        #counter = 1
        for u in cur:

            if u["u.id"] not in users:
                user = {
                    'uid': u["u.id"],
                    'screen_name': u['u.screen_name'],
                    'friends_count': u['u.friends_count'],
                    'followers_count': u['u.followers_count'],
                    'length': u['u.term_count'],
                    'tscore': 0.0,
                    'pscore': (u['u.{0}'.format(pr_type)] - pravg) / prstdev,
                    'tokens': [ ]
                }
                users[u["u.id"]] = user

            users[u["u.id"]]['tokens'].append(i)

            #if counter % 1000 == 0:
            #    print ">> Processed {0} users".format(counter)
            #u_id = user["u.id"]
            # terms = user["u.terms"]
            #length = user["u.term_count"]
            # Term frequency for 'user'
            # q = "{0}:".format(token)
            # idx = terms.find(q)
            # sub = terms[(idx + len(q)):]
            # user_count = int(sub[:sub.find(" ")])
            #user_count = user["d.count"]
            users[u["u.id"]]['tscore'] += wtq * u['d.count']

            '''wtd = user_count
            if user['uid'] in users:
                users[user['uid']]['tscores'] += wtq * wtd
            else:
                #p_scores[u_id] = (user['u.{0}'.format(pr_type)] - pravg) / prstdev
                #lengths[u_id] = length
                users[user['uid']]['tscores'] = wtq * wtd
            counter += 1'''
        i += 1

    # Normalize scores by document size (user length)
    for user in users.values():
        # Normalize by square root of length
        user['tscore'] = user['tscore'] / math.sqrt(user['length'])

    # Normalize to avg = 0 and stdev = 1
    u = users.keys()
    l = [users[k]['tscore'] for k in users.keys()]
    l = np.asarray(l) - np.mean(l)
    l = l / np.std(l)

    for i, uid in enumerate(u):
        users[uid]['tscore'] = l[i]
        users[uid]['score'] = users[uid]['tscore'] * alpha + users[uid]['pscore'] * (1.0 - alpha)
        #users[uid]['score'] = users[uid]['tscore']

    ret = sorted(users.values(), key=lambda k: k['score'], reverse=True)

    #ret = sorted(ret, key=lambda k: k['score'], reverse = True)
    return ret[:limit]

if __name__ == '__main__':
    query = "donald trump"
    result = recommend(query, alpha=0.5, pr_type='rankb')
    #sorted_x = sorted(result.items(), key = operator.itemgetter(1), reverse = True)
    print result
