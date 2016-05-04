# -*- coding: utf-8 -*-

import os
import requests
import urllib

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
    woeid = 23424977 # Where on Earth ID for the USA
    url = "https://api.twitter.com/1.1/trends/place.json?id={woeid}".format(woeid=woeid)
    headers = dict(accept="application/json", Authorization="Bearer " + token)

    r = requests.get(url, headers=headers)
    trends = r.json()[0]["trends"]

    return trends


def find_tweets(topic, since_id, token):
    import urllib as urlb

    base_url = "https://api.twitter.com/1.1/search/tweets.json?"
    headers = dict(accept="application/json", Authorization="Bearer " + token)

    payload = dict(
        count=500,
        result_type="recent",
        lang="en",
        q=urlb.quote(topic),
        since_id=since_id
    )

    url = base_url + "q={q}&count={count}&result_type={result_type}&lang={lang}&since_id={since_id}".format(**payload)

    r = requests.get(url, headers=headers)
    tweets = r.json()["statuses"]

    return tweets

def get_user_profile_image_url(user_id, token):
    params = dict(
        user_id=user_id,
    )
    url = get_url("users/show", params)
    res = authenticated_request(url, token)
    if "profile_image_url" in res:
        return res["profile_image_url"].replace("_normal", "_bigger")
    else:
        return None

def get_url(path, params):
    query = urllib.urlencode(params)
    return "https://api.twitter.com/1.1/users/show.json?" + query

def authenticated_request(url, token):
    headers = dict(
        accept="application/json",
        Authorization="Bearer " + token,
    )
    res = requests.get(url, headers=headers)
    return res.json()
