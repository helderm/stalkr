import os
import time
import random as rnd
from py2neo import Graph, Relationship, authenticate
from celery import Celery
from celery.utils.log import get_task_logger

import twitter as tw

# init celery
logger = get_task_logger(__name__)
mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
logger.info('Initializing Celery using [{}] as a broker...', mongodb_url + 'celery')
app = Celery(include=[ 'stalkr.tasks' ], broker=mongodb_url + 'celery')
try:
    app.config_from_object('stalkr.celeryconfig', force=True)
except Exception as e:
    app.config_from_object('celeryconfig', force=True)

# set up db
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '17474')
logger.info('Connecting to Neo4j at {0}:{1}', neodb, neoport)
authenticate(neodb + ':' + neoport, "neo4j", "neo4j")
graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

def upload_tweets(tweets, graph):
    for t in tweets:
        u = t["user"]
        e = t["entities"]

        tweet = graph.merge_one("Tweet", "id", t["id"])
        tweet.properties["text"] = t["text"]
        tweet.push()

        user = graph.merge_one("User", "username", u["screen_name"])
        graph.create_unique(Relationship(user, "POSTS", tweet))

        for h in e.get("hashtags", []):
            hashtag = graph.merge_one("Hashtag", "name", h["text"].lower())
            graph.create_unique(Relationship(hashtag, "TAGS", tweet))

        for m in e.get('user_mentions', []):
            mention = graph.merge_one("User", "username", m["screen_name"])
            graph.create_unique(Relationship(tweet, "MENTIONS", mention))

        reply = t.get("in_reply_to_status_id")

        if reply:
            reply_tweet = graph.merge_one("Tweet", "id", reply)
            graph.create_unique(Relationship(tweet, "REPLY_TO", reply_tweet))

        ret = t.get("retweeted_status", {}).get("id")

        if ret:
            retweet = graph.merge_one("Tweet", "id", ret)
            graph.create_unique(Relationship(tweet, "RETWEETS", retweet))

@app.task
def import_tweets():
    TWITTER_BEARER = tw.get_bearer()

    # setup db
    graph.cypher.execute("CREATE CONSTRAINT ON (u:User) ASSERT u.username IS UNIQUE")
    graph.cypher.execute("CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE")
    graph.cypher.execute("CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE")

    since_id = -1

    # get trending topics
    #trends = tw.find_trending_topics(TWITTER_BEARER)

    hashtags = ['#FeelTheBern', '#Bernie2016', '#BernieSanders', '#NotMeUs', '#Bernie',
                '#UniteBlue', '#StillSanders', '#NYPrimary', '#WIPrimary', '#ImWithHer',
                '#Hillary2016', '#HillaryClinton', '#Hillary', '#Trump2016',
                '#MakeAmericaGreatAgain', '#TrumpTrain', '#Trump', '#tcot',
                '#AlwaysTrump', '#TeamTrump', '#WakeUpAmerica', '#ccot', '#TeaParty',
                '#DonaldTrump', '#TedCruz', '#CruzCrew', '#Cruz2016', '#PJNET',
                '#elections2016', '#vote', '#cir', '#USlatino', '#AINF', '#Latinos'
                '#GOP', '#2016Election', '#ImmigrationReform']

    for hash in hashtags:
        try:
            tweets = tw.find_tweets(hash, since_id=since_id, token=TWITTER_BEARER)

            if not tweets:
                print "No tweets found."
                continue

            #since_id = tweets[0].get("id")
            upload_tweets(tweets, graph)

            print("[{}] tweets from trend [{}] uploaded!".format(len(tweets), trend['name']))

        except Exception, e:
            logger.exception(e)
            time.sleep(10)
            continue

@app.task
def compute_pagerank():
    WALKS_PER_USER = 1
    BORED = 0.15

    total_steps = 0
    users_count = {}

    # get the count of users in the db
    total_users = graph.cypher.execute('MATCH (n:User) RETURN DISTINCT count(n)')
    total_users = total_users[0]['count(n)']

    # for each user of the db
    for wlk in range(WALKS_PER_USER):
        for user in graph.find(label='User'):
            username = user['username']
            print('User = ' + username)

            while True:
                total_steps += 1

                if username not in users_count:
                    users_count[username] = 0

                users_count[username] += 1

                if rnd.random() < BORED:
                    break

                # stop following users if im bored
                mentions = []
                query = 'MATCH (u:User \{username: {0}\})-[p:POSTS]->(t:Tweet)-[r:MENTIONS]->(n:User) RETURN n'\
                            .format(username)

                for mention in graph.cypher.execute(query):
                    mentions.add(mention['username'])

                # if it is a sink, jump!
                if len(mentions) == 0:
                    query = 'MATCH (u:User) RETURN u, rand() as r ORDER BY r LIMIT 1'
                    username = graph.cypher.execute(query)[0]['u']['username']
                    continue

                # get all tweets with mentions


                # following a user mention with equal probability


if __name__ == '__main__':
    compute_pagerank()
