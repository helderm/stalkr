import os
import json
import random as rnd
from py2neo import Graph, authenticate
import math

shutdown = False
FILENAME = 'ranker.json'
LIMIT = 100

def compute_pagerank():
    print('Initializing PageRank calculation...')

    # set up db
    neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
    neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
    print('Connecting to Neo4j at {0}:{1}'.format(neodb, neoport))
    authenticate(neodb + ':' + neoport, "neo4j", "neo4j")
    graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

    pr_meta = recover_pagerank()

    try:
        # for each walk
        wlk_init = pr_meta['walk']
        for wlk in range(wlk_init, args.walks+1):
            if pr_meta['status'] != 'walking':
                break

            print('Intializing walk #{0}'.format(wlk))
            pr_meta['walk'] = wlk

            # for each user of the db
            while True:
                query = 'MATCH (u:User) RETURN u ORDER BY u.screen_name ' \
                        'SKIP {1} LIMIT {0}'.format(LIMIT, pr_meta['total_users'])

                users = graph.cypher.execute(query)
                if not len(users):
                    break

                for user in users:
                    username = user['u']['screen_name']

                    # while im not bored
                    while True:
                        pr_meta['total_steps'] += 1

                        if username not in pr_meta['users']:
                            pr_meta['users'][username] = 0

                        pr_meta['users'][username] += 1

                        # stop following users if im bored
                        if rnd.random() < args.bored:
                            break

                        # get all tweets with mentions
                        mentions = []
                        query = 'MATCH (u:User {{screen_name: \'{0}\'}})-[p:POSTS]->(t:Tweet)-[r:MENTIONS]->(n:User) ' \
                                'RETURN n'.format(username)

                        for mention in graph.cypher.execute(query):
                            mentions.append(mention['n']['screen_name'])

                        # if it is a sink, jump!
                        if len(mentions) == 0:
                            query = 'MATCH (u:User) RETURN u, rand() as r ORDER BY r LIMIT 1'
                            username = graph.cypher.execute(query)[0]['u']['screen_name']
                            continue

                        # choose another mentioned user randomly
                        username = rnd.choice(mentions)

                    pr_meta['total_users'] += 1

                    if shutdown:
                        save_and_shutdown(pr_meta)

                print('[{0}] users ranked, [{1}] steps taken so far...'.format(pr_meta['total_users'], pr_meta['total_steps']))

            pr_meta['total_users'] = 0

        print('Saving [{0}] ranks into the db...'.format(len(pr_meta['users'])))
        pr_meta['status'] = 'saving'

        # calculate and save the ranks
        users_saved = []
        for username, count in pr_meta['users'].iteritems():
            rank = math.log(count / float(pr_meta['total_steps']))

            query = 'MATCH (u:User {{screen_name: \'{0}\'}}) RETURN u'.format(username)
            user = graph.cypher.execute(query)
            user = user[0]['u']
            user['rank'] = rank
            user.push()
            users_saved.append(username)

            if len(users_saved) % 1000 == 0:
                print('[{0}] users saved so far...'.format(len(users_saved)))

            if shutdown:
                # remove the ranks that we already stored
                for k in users_saved:
                    pr_meta['users'].pop(k, None)

                save_and_shutdown(pr_meta)

        silentremove(FILENAME)

    except Exception as e:
        print('Unknown exception happened!')
        silentremove(FILENAME)

    print('PageRank finished!')


def recover_pagerank():
    # try to load the serialized counts
    try:
        with open(FILENAME) as data_file:
            pr_meta = json.load(data_file)

        assert(pr_meta['bored'] == args.bored)
        assert(pr_meta['total_walks'] == args.walks)

        print('File {0} recovered! Resuming PageRank...'.format(FILENAME))
    except:
        silentremove(FILENAME)
        pr_meta = {
            'bored': args.bored,
            'total_walks': args.walks,
            'total_steps': 0,
            'total_users': 0,
            'users': {},
            'status': 'walking',
            'walk': 1
        }

    return pr_meta


def silentremove(filename):
    import errno
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise


def handler(signum, frame):
    global shutdown
    print('PageRank shutdown requested! Finalizing...')
    shutdown = True


def save_and_shutdown(pr):
    print('PageRank interrupted! Serializing dicts...')
    with open(FILENAME, 'w') as outfile:
        json.dump(pr, outfile, indent=4, sort_keys=True)
    print('PageRank finished!')
    import sys
    sys.exit(0)

if __name__ == '__main__':
    import argparse
    import signal

    # parse command line args
    parser = argparse.ArgumentParser(description='PageRank MonteCarlo')
    parser.add_argument('--walks', default=2, type=int, help='Total number of walks performed over all users')
    parser.add_argument('--bored', default=0.15, type=float, help='Probability of getting bored in the random walk')
    args = parser.parse_args()

    # register signal handlers
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    # start the pageranking
    compute_pagerank()
