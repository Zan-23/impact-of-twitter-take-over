# import csv
# import datetime
# import json
# import os
# import random
# import re
# import time
# from pathlib import Path
#
# import numpy as np
# import pandas as pd
# import requests
# import tweepy
# from dotenv import load_dotenv
#
#
# def main(total_amount_of_tweets=100):
#     search_query = "Elon musk"
#     headers = ["tweet_id", "lang", "author_id", "created_at", "source", "text", "geo", "retweet_count", "reply_count",
#                "like_count", "quote_count"]
#     start_date = datetime.datetime.strptime("01/06/2022 00:00", "%d/%m/%Y %H:%M")
#     end_date = datetime.datetime.strptime("06/06/2022 00:00", "%d/%m/%Y %H:%M")
#     print(f"Started search for tweet query '{search_query}' in date range: {start_date} -> {end_date}")
#
#     tweets_per_day, date_ranges = partition_tweets_by_days(total_amount_of_tweets=total_amount_of_tweets,
#                                                            start_time=start_date, end_time=end_date)
#     # prepare twitter client
#     client = prepare_twitter_clients()
#
#     # TODO add saving to file when array to big to fit in memory
#     loaded_tweets_arr = []
#     request_count = 0
#     start_time = time.time()
#     for start_date_i, end_date_i in date_ranges:
#         print(f"\nCollecting '{tweets_per_day}' tweets for date range: {start_date_i} -> {end_date_i}")
#         try:
#             query_params = prepare_query_parameters(max_results=tweets_per_day,
#                                                     start_time=start_date_i, end_time=end_date_i)
#             # TODO pay attention to not exceed 15 minute query limits (900 requests per 15 minutes?)
#             tweets = client.search_all_tweets(search_query, **query_params)
#
#             for i, tweet in enumerate(tweets.data):
#                 print(f"Tweet: {i + 1}")
#                 current_tweet = extract_information_from_tweet(tweet)
#                 loaded_tweets_arr.append(current_tweet)
#
#             request_count += 1
#             time.sleep(0.5 + random.random() * 2)
#         # catch Twitter API errors
#         except tweepy.errors.TooManyRequests as e:
#             # TODO
#             print(f"Too many requests 'e'! At request count: {request_count}")
#             break
#         if request_count > 300:
#             print("Request limit reached, waiting 15 minutes")
#             time.sleep(15 * 60)
#
#     print(f"Finished collecting tweets in {time.time() - start_time} seconds")
#     tweet_df = pd.DataFrame(loaded_tweets_arr)
#     tweet_df.columns = headers
#     tweet_df.to_csv("tweets.csv", index=False)
#     print(f"Saved tweets to file: tweets.csv")
#
#
# def prepare_query_parameters(query, max_results, start_time, end_time):
#     # no spaces between words in fields!
#     params = {"query": query,
#               "max_results": max_results,
#               "start_time": start_time,
#               "end_time": end_time,
#               "tweet_fields": "id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,lang,"
#                               "public_metrics,referenced_tweets,reply_settings,source",
#               "user_fields": "id,name,username,created_at,description,public_metrics,verified",
#               "place_fields": "full_name,id,country,country_code,geo,name,place_type",
#               }
#     return params
#
#
# def prepare_twitter_clients():
#     dotenv_path = Path(".env")
#     load_dotenv(dotenv_path=dotenv_path)
#
#     # consumer_key = os.environ.get("API_KEY")
#     # consumer_secret = os.environ.get("API_KEY_SECRET")
#     # access_token = os.environ.get("ACCESS_TOKEN")
#     # access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
#     bearer_token = os.environ.get("BEARER_TOKEN")
#     print(f"Loaded bearer token ... ")
#
#     client = tweepy.Client(bearer_token=bearer_token)
#     print("Client created\n")
#     return client
#
# # def query_tweets(query, client):
# #     # Replace with your own search query
# #     query = 'from:suhemparack -is:retweet'
# #
# #     tweets = client.search_recent_tweets(query=query, tweet_fields=['context_annotations', 'created_at'],
# #                                          max_results=100)
# #
# #     print("Tweet time")
# #     for tweet in tweets.data:
# #         print(tweet.text)
# #         if len(tweet.context_annotations) > 0:
# #             print(tweet.context_annotations)
# #         break
