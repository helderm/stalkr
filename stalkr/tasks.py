import os
import time
import requests
from py2neo import Graph, Relationship, authenticate

from celery import Celery
from celery.utils.log import get_task_logger

# init celery
logger = get_task_logger(__name__)
mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
print('Initializing Celery using [{}] as a broker...', mongodb_url + 'celery')
app = Celery(include=[ 'stalkr.tasks' ], broker=mongodb_url + 'celery')
app.config_from_object('stalkr.celeryconfig')

# set up db
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
print('Connecting to Neo4j at {0}:{1}', neodb, neoport)
authenticate(neodb + ':' + neoport, "neo4j", "neo4j")
graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

def get_bearer():
    if os.environ.get('TWITTER_BEARER', None) is not None:
        return os.environ.get('TWITTER_BEARER')

    # base64 encoded key and secret
    basic = 'M2NWQ0xYdHF3bzdSc3RPcTY4VWNLUFI0SjpHSktwVlYzU2UxTzdwYm9aMFcyeWFZNHJJWVRFNDVWQVF6WktjV203eWE3VzJLejRMZw=='

    url = 'https://api.twitter.com/oauth2/token'
    headers = {'Authorization': 'Basic ' + basic,
               'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
    body = {'grant_type': 'client_credentials'}

    ret = requests.post(url, data=body, headers=headers)

    bearer = ret.json()['access_token']
    os.environ['TWITTER_BEARER'] = str(bearer)
    return bearer


def find_trending_topics(token):
    woeid = 12 # Where on Earth ID for the USA
    url = "https://api.twitter.com/1.1/trends/place.json?id={woeid}".format(woeid=woeid)
    headers = dict(accept="application/json", Authorization="Bearer " + token)

    r = requests.get(url, headers=headers)
    trends = r.json()[0]["trends"]

    return trends


def find_tweets(topic, since_id, token):
    base_url = "https://api.twitter.com/1.1/search/tweets.json?"
    headers = dict(accept="application/json", Authorization="Bearer " + token)

    payload = dict(
        count=100,
        result_type="recent",
        lang="en",
        q=topic,
        since_id=since_id
    )

    url = base_url + "q={q}&count={count}&result_type={result_type}&lang={lang}&since_id={since_id}".format(**payload)

    r = requests.get(url, headers=headers)
    tweets = r.json()["statuses"]

    return tweets


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
    TWITTER_BEARER = get_bearer()

    # setup db
    graph.cypher.execute("CREATE CONSTRAINT ON (u:User) ASSERT u.username IS UNIQUE")
    graph.cypher.execute("CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE")
    graph.cypher.execute("CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE")

    since_id = -1

    # get trending topics
    trends = find_trending_topics(TWITTER_BEARER)

    for trend in trends:
        try:
            tweets = find_tweets(trend['query'], since_id=since_id, token=TWITTER_BEARER)

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

if __name__ == '__main__':
    import_tweets()
