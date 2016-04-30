# -*- encoding: utf-8 -*-
import time
import base64
import requests
import os
import json
from py2neo import Graph, Relationship, authenticate, Node
import sys
import urllib
import topics
import sentiment

#get hashtags from file
with open('hashtags.txt') as f:
    hashtags = f.readlines()

hashtags_string = "";

for i in range(0, len(hashtags)):
    hashtags[i] = hashtags[i].replace("\n", "").lower()
    if i == len(hashtags) - 1:
        hashtags_string += hashtags[i]
    else:
        hashtags_string += hashtags[i] + " OR "

print(">> Hashtag Query built: " + hashtags_string)

hashtags_string = urllib.quote_plus(hashtags_string)

print(">> Query URL: " + hashtags_string)

# set up neo4j
neodb = os.getenv('OPENSHIFT_NEO4J_DB_HOST', 'localhost')
neoport = os.getenv('OPENSHIFT_NEO4J_DB_PORT', '7474')
print('Connecting to Neo4j at {0}:{1}', neodb, neoport)
authenticate(neodb + ':' + neoport, "neo4j", "1234")
graph = Graph('http://{0}:{1}/db/data/'.format(neodb, neoport))

# rate limiting
TWEET_INDIRECT_BITS = 1
TWEET_DIRECT_BITS = 2
USER_DIRECT_BITS = 4

LIMIT_COUNT = 0
LIMIT_VAL = 1
LIMIT_DEADLINE = 2

tweet_indirect = [-1, -1, -1]
tweet_direct = [-1, -1, -1]
user_direct = [-1, -1, -1]

# timeline controls
USE_SINCE_ID = 1
USE_MAX_ID = 2
max_id = - sys.maxint - 1
since_id = - sys.maxint - 1
min_id = sys.maxint
id_policy_bits = 0

def get_bearer():
    if os.environ.get('TWITTER_BEARER', None) is not None:
        return os.environ.get('TWITTER_BEARER')

    # base64 encoded app credentials from dev.twitter.com
    basic = 'Z0VoZGwzMTd2R3R1dzY2NUxXWFhvblY5UzpFYjkxTmU0S0VoWU9pUDMyVzNQa3RvQVJ6d1N6M0c4NEhNTWUyUTNTUXczdGxQeWhxQw=='

    url = 'https://api.twitter.com/oauth2/token'
    headers = {'Authorization': 'Basic ' + basic,
               'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
    body = {'grant_type': 'client_credentials'}

    ret = requests.post(url, data = body, headers = headers)

    bearer = ret.json()['access_token']
    os.environ['TWITTER_BEARER'] = str(bearer)

    return bearer

def get_trending_topics(token):
    url = "https://api.twitter.com/1.1/trends/place.json?id=1"
    headers = dict(accept = "application/json", Authorization = "Bearer " + token)

    r = requests.get(url, headers = headers, timeout = 10)
    data = r.json()[0]["trends"]

    return data

def get_user_data(id, token):
    if user_direct[LIMIT_COUNT] >= user_direct[LIMIT_VAL]:
        print ">> Direct user - rate limited! {0}/{1}...".format(user_direct[LIMIT_COUNT], user_direct[LIMIT_VAL])
        return None
    else:
        print ">> Getting direct user {0}/{1}...".format(user_direct[LIMIT_COUNT], user_direct[LIMIT_VAL])

    url = "https://api.twitter.com/1.1/users/show.json?screen_name=" + id
    headers = dict(accept = "application/json", Authorization = "Bearer " + token)

    r = requests.get(url, headers = headers, timeout = 10)
    data = r.json()

    user_direct[LIMIT_COUNT] += 1

    return data

def get_rate_limits(token, mask):
    print ">> Retrieving rate limits from twitter API..."
    url = "https://api.twitter.com/1.1/application/rate_limit_status.json?resources=users,application,search,statuses"

    headers = dict(accept = "application/json", Authorization = "Bearer " + token)

    r = requests.get(url, headers = headers, timeout = 10)
    data = r.json()["resources"]

    if mask & TWEET_INDIRECT_BITS > 0:
        tweet_indirect[LIMIT_COUNT] = 0
        tweet_indirect[LIMIT_VAL] = data["search"]["/search/tweets"]["remaining"]
        tweet_indirect[LIMIT_DEADLINE] = data["search"]["/search/tweets"]["reset"]
        print ">> Indirect tweet limits [count:{0}, limit:{1}, deadline:{2}]".format(tweet_indirect[0], tweet_indirect[1], tweet_indirect[2])

    if mask & TWEET_DIRECT_BITS > 0:
        tweet_direct[LIMIT_COUNT] = 0
        tweet_direct[LIMIT_VAL] = data["statuses"]["/statuses/show/:id"]["remaining"]
        tweet_direct[LIMIT_DEADLINE] = data["statuses"]["/statuses/show/:id"]["reset"]
        print ">> Direct tweet limits [count:{0}, limit:{1}, deadline:{2}]".format(tweet_direct[0], tweet_direct[1], tweet_direct[2])

    if mask & USER_DIRECT_BITS > 0:
        user_direct[LIMIT_COUNT] = 0
        user_direct[LIMIT_VAL] = data["users"]["/users/show/:id"]["remaining"]
        user_direct[LIMIT_DEADLINE] = data["users"]["/users/show/:id"]["reset"]
        print ">> Direct user limits [count:{0}, limit:{1}, deadline:{2}]".format(user_direct[0], user_direct[1], user_direct[2])

def get_tweet(token, id):
    if tweet_direct[LIMIT_COUNT] >= tweet_direct[LIMIT_VAL]:
        print ">> Direct tweet - rate limited! {0}/{1}...".format(tweet_direct[LIMIT_COUNT], tweet_direct[LIMIT_VAL])
        return None
    else:
        print ">> Getting direct tweet {0}/{1}...".format(tweet_direct[LIMIT_COUNT], tweet_direct[LIMIT_VAL])

    url = "https://api.twitter.com/1.1/statuses/show.json?id={0}".format(id)

    headers = dict(accept = "application/json", Authorization = "Bearer " + token)

    r = requests.get(url, headers = headers, timeout = 10)
    data = r.json()

    tweet_direct[LIMIT_COUNT] += 1

    return data

def get_tweets(token):
    if tweet_indirect[LIMIT_COUNT] >= tweet_indirect[LIMIT_VAL]:
        print ">> Indirect tweets - rate limited! {0}/{1}".format(tweet_indirect[LIMIT_COUNT], tweet_indirect[LIMIT_VAL])
        return None
    else:
        print ">> Getting indirect tweets {0}/{1}...".format(tweet_indirect[LIMIT_COUNT], tweet_indirect[LIMIT_VAL])

    base_url = "https://api.twitter.com/1.1/search/tweets.json?"
    headers = dict(accept="application/json", Authorization="Bearer " + token)

    payload = dict(
        count = 100,
        result_type = "recent",
        lang = "en",
        q = hashtags_string
    )

    url = base_url + "q={q}&count={count}&result_type={result_type}&lang={lang}".format(**payload)

    if id_policy_bits & USE_MAX_ID > 0:
        url = url + "&max_id={0}".format(min_id - 1) # avoid single repetition

    if id_policy_bits & USE_SINCE_ID > 0:
        url = url + "&since_id={0}".format(since_id)

    r = requests.get(url, headers = headers, timeout = 10)
    data = r.json()["statuses"]

    tweet_indirect[LIMIT_COUNT] += 1

    return data

def check_rates(token):
    if time.time() > tweet_indirect[LIMIT_DEADLINE]:

        get_rate_limits(token, TWEET_INDIRECT_BITS)
        id_policy_bits = USE_SINCE_ID
        since_id = max_id
        print ">> tweet_indirect rate updated!"
        print tweet_indirect

    if time.time() > tweet_direct[LIMIT_DEADLINE]:
        get_rate_limits(token, TWEET_DIRECT_BITS)
        print ">> tweet_direct rate updated!"
        print tweet_direct

    if time.time() > user_direct[LIMIT_DEADLINE]:
        get_rate_limits(token, USER_DIRECT_BITS)
        print ">> user_direct rate updated!"
        print user_direct

# this is where we should use nltk to obtain the topics
def process_text(data):
    tokens = topics.get_topics(data)
    return tokens

# ids = []

def push_tweet(data, timelineable):
    global max_id
    global min_id
    global id_policy_bits

    id = data["id"]

    # merge tweet by id
    tweet = graph.merge_one("Tweet", "id", id)

    # timelining stuff
    if timelineable:
        if id > max_id:
            max_id = id

        if id < min_id:
            min_id = id
            id_policy_bits = id_policy_bits | USE_MAX_ID

    # authorship
    if "user" in data:
        user = push_user(data["user"])
        graph.create_unique(Relationship(user, "POSTS", tweet))

    # quotes
    if "quoted_status" in data:
        tweet2 = push_tweet(data["quoted_status"], False)
        graph.create_unique(Relationship(tweet, "QUOTES", tweet2))

    # is a retweet
    if "retweeted_status" in data:
        tweet2 = push_tweet(data["retweeted_status"], False)
        graph.create_unique(Relationship(tweet, "RETWEETS", tweet2))

    # reply
    reply = data.get("in_reply_to_status_id")

    if reply:
        reply_tweet = graph.merge_one("Tweet", "id", data["in_reply_to_status_id"])
        graph.create_unique(Relationship(tweet, "REPLY_TO", reply_tweet))

    # geolocation exact/estimated
    if data["coordinates"] is not None:
        tweet.properties["lon"] = data["coordinates"]["coordinates"][0]
        tweet.properties["lat"] = data["coordinates"]["coordinates"][1]
    elif data["place"] is not None:
        coordinates = data["place"]["bounding_box"]["coordinates"][0]
        lon = (coordinates[0][0] + coordinates[1][0] + coordinates[2][0] + coordinates[3][0]) / 4
        lat = (coordinates[0][1] + coordinates[1][1] + coordinates[2][1] + coordinates[3][1]) / 4
        tweet.properties["lon"] = lon
        tweet.properties["lat"] = lat

    # fav count
    tweet.properties["favorite_count"] = data["favorite_count"]

    # rt count
    tweet.properties["retweet_count"] = data["retweet_count"]

    # text
    tweet.properties["text"] = data["text"]
    if "user" in data and parse_terms:
        for tok in process_text(data["text"]):
            word = push_word(tok)
            rel = graph.match_one(user, "DISCUSSES", word)
            if rel:
                rel.properties["count"] = rel.properties["count"] + 1
                rel.push()
            else:
                rel = Relationship(user, "DISCUSSES", word)
                rel.properties["count"] = 1
                graph.create_unique(rel)

    if "text" in data:
        sent = sentiment.get_sentiment(data["text"])
        tweet["polarity"] = sent[0]
        tweet["subjectivity"] = sent[1]

    # hashtags
    for h in data["entities"].get("hashtags", []):
        hashtag = push_hashtag(h)
        graph.create_unique(Relationship(hashtag, "TAGS", tweet))

    # mentions
    for m in data["entities"].get("user_mentions", []):
        mention = push_user(m)
        graph.create_unique(Relationship(tweet, "MENTIONS", mention))

    tweet.push()

    return tweet

def push_word(data):
    term = graph.merge_one("Word", "name", data)
    return term

def push_hashtag(data):
    hashtag = graph.merge_one("Hashtag", "name", data["text"].lower())
    # hashtag.push()
    return hashtag

def push_user(data):
    user = graph.merge_one("User", "id", data["id"])

    user.properties["screen_name"] = data["screen_name"]

    if "followers_count" in data:
        user.properties["followers_count"] = data["followers_count"]

    if "friends_count" in data:
        user.properties["friends_count"] = data["friends_count"]

    if "listed_count" in data:
        user.properties["listed_count"] = data["listed_count"]

    if "statuses_count" in data:
        user.properties["statuses_count"] = data["statuses_count"]

    if " " in data:
        user.properties["verified"] = data["verified"]

    user.push()

    return user

def crawl(token):
    tweets = get_tweets(token)

    for t in tweets:
        push_tweet(t, True)

# --------------------- MAIN --------------------
token = get_bearer()

get_rate_limits(token, TWEET_DIRECT_BITS | TWEET_INDIRECT_BITS | USER_DIRECT_BITS)

graph.cypher.execute("CREATE CONSTRAINT ON (u:User) ASSERT u.id IS UNIQUE")
graph.cypher.execute("CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE")
graph.cypher.execute("CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE")
graph.cypher.execute("CREATE CONSTRAINT ON (w:Word) ASSERT w.name IS UNIQUE")

while 1:
    try:
        crawl(token)
        # get_tweets(token, 0)
        # get_tweet(token, 722575509545185280)
        # get_user_data("costalobo_", token)
        check_rates(token)
    except KeyboardInterrupt:
        sys.exit()
    except requests.exceptions.RequestException:
        print ">> Connection Timeout!"
        pass
    # except Exception, e:
        # time.sleep(10)
        # pass
