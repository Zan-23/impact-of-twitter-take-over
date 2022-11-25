
import os
from pathlib import Path

import tweepy
from dotenv import load_dotenv


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

    tweets = client.search_recent_tweets(query=query, tweet_fields=['context_annotations', 'created_at'], max_results=100)

    print("Tweet time")
    for tweet in tweets.data:
        print(tweet.text)
        if len(tweet.context_annotations) > 0:
            print(tweet.context_annotations)
        break