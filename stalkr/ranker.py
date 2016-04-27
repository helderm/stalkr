import os
import random as rnd
from py2neo import Graph, authenticate

def compute_pagerank():
    print('Initializing PageRank calculation...')

    # set up db
    neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
    neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
    print('Connecting to Neo4j at {0}:{1}', neodb, neoport)
    authenticate(neodb + ':' + neoport, "neo4j", "neo4j")
    graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

    limit = 100
    total_steps = 0
    users_count = {}

    # for each user of the db
    for wlk in range(args.walks):
        print('Intializing walk #{0}'.format(wlk))

        total_users = 0
        while True:
            query = 'MATCH (u:User) RETURN u ORDER BY u.username SKIP {1} LIMIT {0}'.format(limit, total_users)
            users = graph.cypher.execute(query)
            if not len(users):
                break

            for user in users:
                username = user['u']['username']

                while True:
                    total_steps += 1

                    if username not in users_count:
                        users_count[username] = 0

                    users_count[username] += 1

                    # stop following users if im bored
                    if rnd.random() < args.bored:
                        break

                    # get all tweets with mentions
                    mentions = []
                    query = 'MATCH (u:User {{username: \'{0}\'}})-[p:POSTS]->(t:Tweet)-[r:MENTIONS]->(n:User) ' \
                            'RETURN n'.format(username)

                    for mention in graph.cypher.execute(query):
                        mentions.append(mention['n']['username'])

                    # if it is a sink, jump!
                    if len(mentions) == 0:
                        query = 'MATCH (u:User) RETURN u, rand() as r ORDER BY r LIMIT 1'
                        username = graph.cypher.execute(query)[0]['u']['username']
                        continue

                    # choose another mentioned user randomly
                    username = rnd.choice(mentions)

            total_users += limit
            print('[{0}] users ranked, [{1}] steps taken so far...'.format(total_users, total_steps))

    print('Saving [{0}] ranks into the db...'.format(len(users_count)))
    for username, count in users_count.iteritems():
        rank = count / float(total_steps)

        query = 'MATCH (u:User {{username: \'{0}\'}}) RETURN u'.format(username)
        user = graph.cypher.execute(query)
        user = user[0]['u']
        user['rank'] = rank
        user.push()

    print('PageRank finished!')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='PageRank MonteCarlo')
    parser.add_argument('--walks', default=2, type=int, help='Total number of walks performed over all users')
    parser.add_argument('--bored', default=0.15, type=float, help='Probability of getting bored in the random walk')

    args = parser.parse_args()
    compute_pagerank()
