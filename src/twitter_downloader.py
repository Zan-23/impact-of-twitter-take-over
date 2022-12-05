import csv
import datetime
import json
import os
import time
from pathlib import Path

import dateutil
import requests
import tweepy
from dotenv import load_dotenv


def create_url(keyword, start_date, end_date, max_results=10):
    search_url = "https://api.twitter.com/2/tweets/search/all"  # Change to the endpoint you want to collect data from

    # change params based on the endpoint you are using
    query_params = {'query': keyword,
                    'start_time': start_date,
                    'end_time': end_date,
                    'max_results': max_results,
                    'expansions': 'author_id,in_reply_to_user_id,geo.place_id',
                    'tweet.fields': 'id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,'
                                    'lang,public_metrics,referenced_tweets,reply_settings,source',
                    'user.fields': 'id,name,username,created_at,description,public_metrics,verified',
                    'place.fields': 'full_name,id,country,country_code,geo,name,place_type',
                    'next_token': {}}
    return (search_url, query_params)


def connect_to_endpoint(url, headers, params, next_token=None):
    params['next_token'] = next_token  # params object received from create_url function
    response = requests.request("GET", url, headers=headers, params=params)
    print("Endpoint Response Code: " + str(response.status_code))
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def main():
    dotenv_path = Path(".env")
    load_dotenv(dotenv_path=dotenv_path)
    bearer_token = os.environ.get("BEARER_TOKEN")
    consumer_key = os.environ.get("API_KEY")
    consumer_secret = os.environ.get("API_KEY_SECRET")

    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
    print(f"Auth info {consumer_key} {consumer_secret} {access_token} {access_token_secret}")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    start_date = datetime.datetime(2021, 1, 19, 12, 00, 00)
    end_date = datetime.datetime(2021, 1, 19, 13, 00, 00)
    print("Start ... ")
    # api = tweepy.API(auth)

    # tweets = tweepy.Cursor(api.search_tweets, q=search_query, lang="en")
    search_query = 'Elon musk'
    # client = tweepy.Client(consumer_key=consumer_key,
    #                        consumer_secret=consumer_secret,
    #                        access_token=access_token,
    #                        access_token_secret=access_token_secret)
    client = tweepy.Client(bearer_token=bearer_token)
    # no spaces between words in fields!
    params = {"max_results": 10,
              "start_time": start_date,
              "end_time": end_date,
              "tweet_fields": "id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,lang,"
                              "public_metrics,referenced_tweets,reply_settings,source",
              "user_fields": "id,name,username,created_at,description,public_metrics,verified",
              "place_fields": "full_name,id,country,country_code,geo,name,place_type",
    }
    tweets = client.search_all_tweets(search_query, **params)
    for i, tweet in enumerate(tweets.data):
        print(f"\nTweet: {i}")
        print(tweet)
        print(tweet.text)

        tweet_id = tweet["id"]
        lang = tweet["lang"]
        author_id = tweet["author_id"]
        created_at = tweet["created_at"]
        source = tweet["source"]
        text = tweet["text"]
        if "geo" in tweet:
            geo = tweet["geo"]["place_id"]
        else:
            geo = " "

        # metrics
        retweet_count = tweet["public_metrics"]["retweet_count"]
        reply_count = tweet["public_metrics"]["reply_count"]
        like_count = tweet["public_metrics"]["like_count"]
        quote_count = tweet["public_metrics"]["quote_count"]

        res = [author_id, created_at, geo, tweet_id, lang, like_count, quote_count, reply_count, retweet_count, source,
               text]
        print(res)
        print("")

    # tweets = tweepy.Cursor(api.search_tweets,
    #                        q=search_query,
    #                        lang="en",
    #                        since=start_date,
    #                        until=end_date,
    #                        result_type="recent").items(2)


def get_bearer_token():
    dotenv_path = Path(".env")
    load_dotenv(dotenv_path=dotenv_path)
    return os.environ.get("BEARER_TOKEN")


def prepare_twitter_clients():
    dotenv_path = Path("./../.env")
    load_dotenv(dotenv_path=dotenv_path)

    # consumer_key = os.environ.get("API_KEY")
    # consumer_secret = os.environ.get("API_KEY_SECRET")
    # access_token = os.environ.get("ACCESS_TOKEN")
    # access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
    bearer_token = os.environ.get("BEARER_TOKEN")

    # auth = tweepy.OAuth1UserHandler(
    #   consumer_key,
    #   consumer_secret,
    #   access_token,
    #   access_token_secret
    # )
    #
    # api = tweepy.API(auth)
    client = tweepy.Client(bearer_token=bearer_token)
    return client


def query_tweets(query, client):
    # Replace with your own search query
    query = 'from:suhemparack -is:retweet'

    tweets = client.search_recent_tweets(query=query, tweet_fields=['context_annotations', 'created_at'],
                                         max_results=100)

    print("Tweet time")
    for tweet in tweets.data:
        print(tweet.text)
        if len(tweet.context_annotations) > 0:
            print(tweet.context_annotations)
        break
