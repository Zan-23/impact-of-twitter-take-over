import csv
import datetime
import math
import os
import random
import re
import time
from pathlib import Path

import numpy as np
import requests
from dotenv import load_dotenv


def get_api_url():
    """
    :return: Returns the API url for the Twitter API 2
    """
    search_url = "https://api.twitter.com/2/tweets/search/all"
    return search_url


def connect_to_endpoint(url, headers, params):
    """
    Sends a GET request to the Twitter API 2 endpoint, and retrieves the response. If status code is not 200, then it
    raises the exception. It also gets the count of how many request we can make in the next 15-minute window.

    :param url: String. The url of the endpoint.
    :param headers: Dictionary. The headers of the request, should just contain bearer token.
    :param params: Dictionary. The parameters of the request, specified in prepare_parameter_json() function.
    :return: Dictionary/json of the response, Integer of how many requests we can make in the next 15-minute window.
    """
    response = requests.request("GET", url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)

    request_remaining = int(response.headers["x-rate-limit-remaining"])
    return response.json(), request_remaining


def prepare_parameter_json(query, max_results, start_time, end_time, next_token=None):
    """
    Prepares the parameter json for the request to the Twitter API 2 endpoint. The parameters are specified in the
    documentation of the endpoint:
    https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-all

    Time in start_time and end_time should be in RFC 3339 format, e.g. 2021-03-01T00:00:00Z and there has to be
    no space between words in .fields parameters.

    :param query: String. The query to search for.
    :param max_results: Integer. The maximum number of results to return.
    :param start_time: Datetime object. The start time of the time window to search for tweets.
    :param end_time: Datetime object. The end time of the time window to search for tweets.
    :param next_token: TODO
    :return: Dictionary. The parameter json.
    """
    params = {"query": query,
              "max_results": max_results,
              "start_time": start_time.isoformat() + "Z",
              "end_time": end_time.isoformat() + "Z",
              "expansions": "author_id,in_reply_to_user_id,geo.place_id",
              "tweet.fields": "id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,lang,"
                              "public_metrics,referenced_tweets,reply_settings,source",
              "user.fields": "id,name,username,created_at,description,public_metrics,verified",
              "place.fields": "full_name,id,country,country_code,geo,name,place_type",
              "next_token": next_token
              }
    return params


def create_csv_file():
    """
    Creates a csv file with the name of the current date/time and write the column names to it.
    :return: String. The name of the csv file.s
    """
    curr_date = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
    column_names = ["tweet_id", "lang", "author_id", "created_at", "text", "geo", "retweet_count", "reply_count",
                    "like_count", "quote_count"]
    print("Column count: " + str(len(column_names)))
    file_name = f"./data/twitter_dump_at_time_{curr_date}.csv"
    print("Creating csv file: ", file_name)

    with open(file_name, "w", encoding="UTF8", newline="") as f:
        writer = csv.writer(f)
        # write first row which contains the names of the columns, keep it in sync with the order of the data
        writer.writerow(column_names)
    return file_name


def append_to_csv(file_name, tweet_arr):
    with open(file_name, "a", encoding="UTF8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(tweet_arr)


def partition_day_by_tweets(tweets_per_day, start_time, end_time):
    """
    Function is very similar to partition_tweets_by_days, but it also partitions the day by minutes into smaller intervals
    and each interval gets queried separately.

    :param tweets_per_day: Integer. The amount of tweets that should be acquired for each day, if higher than 500,
    the day is split into multiple time intervals.
    :param start_time: Datetime object. The start time of the time window to search for tweets.
    :param end_time: Datetime object. The end time of the time window to search for tweets.
    :return: Array of tuples, Int. Each tuple contains the start and end time of a day and the integer is the amount of
    tweets to get for each day.
    """
    print(f"\n{'-' * 4}DATE PARTIONING{'-' * 60}")
    assert tweets_per_day % 10 == 0, "tweets_per_day must be a multiple of 10"
    # get total amount of days between dates
    total_amount_of_days = (end_time - start_time).days
    print(f"Total amount of days: {total_amount_of_days}")

    # calculate how many intervals need to be computed
    day_splits = math.ceil(tweets_per_day / 500)
    tweets_per_interval = int(tweets_per_day / day_splits)
    # create minute offsets for each interval
    minute_offsets = np.linspace(0, 1440, day_splits + 1, dtype=int)
    print(f"Day splits: {day_splits}, tweets per interval: {tweets_per_interval}")
    print(f"Minute offsets ({len(minute_offsets) - 1} intervals): \n{minute_offsets}")

    # create date ranges
    day_ranges = []
    for day_offset in range(total_amount_of_days):
        curr_day = start_time + datetime.timedelta(days=day_offset)
        for i, value in enumerate(minute_offsets[:-1]):
            start_time_i = curr_day + datetime.timedelta(minutes=int(value))
            end_time_i = curr_day + datetime.timedelta(minutes=int(minute_offsets[i + 1]))
            day_ranges.append((start_time_i, end_time_i))

    print(f"Created {len(day_ranges)} day partitions, start date: {day_ranges[0][0]}, end date: {day_ranges[-1][1]}")
    print(f"At least {len(day_ranges) * tweets_per_interval} tweets will be acquired!")
    print(f"{'-' * 79}\n")
    return tweets_per_interval, day_ranges


def partition_tweets_by_days(total_amount_of_tweets, start_time, end_time):
    """
    Function creates an array of tuples, where each tuple contains the start and end time of a day. It also assigns an
    equal number of tweets to get for each day.

    :param total_amount_of_tweets: Integer. The total amount of tweets to get.
    :param start_time: Datetime object. The start time of the time window to search for tweets.
    :param end_time: Datetime object. The end time of the time window to search for tweets.
    :return: Array of tuples, Int. Each tuple contains the start and end time of a day and the integer is the amount of
    tweets to get for each day.
    """
    print(f"\n{'-' * 4}DATE PARTIONING{'-' * 60}")
    # get total amount of days between dates
    total_amount_of_days = (end_time - start_time).days
    print(f"Total amount of days: {total_amount_of_days}")

    tweets_per_day = int((total_amount_of_tweets - (total_amount_of_tweets % total_amount_of_days))
                         / total_amount_of_days)
    assert 500 >= tweets_per_day >= 10, "Amount of tweets per day must be greater than 10 and smaller than 500, " \
                                        "else query will fail"
    print(f"There will be {tweets_per_day} collected for each day in range")

    # create date ranges
    day_ranges = []
    for day_offset in range(total_amount_of_days):
        start_time_i = start_time + datetime.timedelta(days=day_offset)
        end_time_i = start_time_i + datetime.timedelta(days=1)
        day_ranges.append((start_time_i, end_time_i))

    print(f"Created {len(day_ranges)} day partitions, start date: {day_ranges[0][0]}, end date: {day_ranges[-1][1]}")
    print(f"{'-' * 79}\n")
    return tweets_per_day, day_ranges


def extract_information_from_tweet(tweet):
    tweet_id = tweet["id"]
    lang = tweet["lang"]
    author_id = tweet["author_id"]
    created_at = tweet["created_at"]
    # source = tweet["source"]
    text = re.sub(r"\s\s+", " ", tweet["text"].strip())
    if "geo" in tweet:
        if "place_id" in tweet["geo"]:
            geo = tweet["geo"]["place_id"]
        else:
            geo = np.nan
    else:
        geo = np.nan

    # metrics
    retweet_count = tweet["public_metrics"]["retweet_count"]
    reply_count = tweet["public_metrics"]["reply_count"]
    like_count = tweet["public_metrics"]["like_count"]
    quote_count = tweet["public_metrics"]["quote_count"]

    return [tweet_id, lang, author_id, created_at, text, geo, retweet_count, reply_count, like_count, quote_count]


def get_bearer_token():
    dotenv_path = Path(".env")
    load_dotenv(dotenv_path=dotenv_path)
    return os.environ.get("BEARER_TOKEN")


def download_tweets(search_query, tweets_per_day, start_time="01/06/2022 00:00", end_time="03/06/2022 00:00"):
    """
    Main function of the script. It gets the bearer token, prepares the parameter json, and generate an array of date
    start and date end. It then iterates through the array and makes a request to the Twitter API 2 endpoint, for each
    range and gets certain amount of tweets from it. It then writes the tweets to a csv file.

    Info for building queries: https://developer.twitter.com/en/docs/twitter-api/tweets/counts/integrate/build-a-query
    Info for status codes: https://developer.twitter.com/en/docs/twitter-api/rate-limits#headers-and-codes

    :param search_query: String. The query to search for tweets.
    :param tweets_per_day: Integer. The total amount of tweets to retrieve.
    :param start_time: String. The start time of the time window to search for tweets. In the format dd/mm/yyyy hh:mm.
    :param end_time: String. The end time of the time window to search for tweets. In the format dd/mm/yyyy hh:mm.
    """
    bearer_token = get_bearer_token()
    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    # put it out to get replies,
    # -is:reply -is:retweet -is:quote -> ensures we only get original tweets
    start_date = datetime.datetime.strptime(start_time, "%d/%m/%Y %H:%M")
    end_date = datetime.datetime.strptime(end_time, "%d/%m/%Y %H:%M")
    print(f"Started search for tweet query '{search_query}' in date range: {start_date} -> {end_date}")

    # this code is for getting a total amount of tweets
    # tweets_per_day, date_ranges = partition_tweets_by_days(total_amount_of_tweets=total_amount_of_tweets,
    #                                                        start_time=start_date, end_time=end_date)
    tweets_per_day, date_ranges = partition_day_by_tweets(tweets_per_day=tweets_per_day, start_time=start_date,
                                                          end_time=end_date)
    loaded_tweets_arr = []
    csv_file_name = create_csv_file()
    twitter_api_url = get_api_url()
    start_time = time.time()
    for start_time_i, end_time_i in date_ranges:
        next_token = None
        tmp_tweets_per_day = tweets_per_day
        while True:
            query_params = prepare_parameter_json(query=search_query, max_results=tmp_tweets_per_day,
                                                  start_time=start_time_i, end_time=end_time_i, next_token=next_token)

            json_response, req_remaining = connect_to_endpoint(twitter_api_url, headers, query_params)
            if "data" not in json_response is None or len(json_response["data"]) == 0:
                print("No data found")
                break
            print(f"\nCollected '{len(json_response['data'])}' (should be {tmp_tweets_per_day}) "
                  f"tweets for date range: {start_time_i} -> {end_time_i}")

            for i, tweet in enumerate(json_response["data"]):
                current_tweet = extract_information_from_tweet(tweet)
                loaded_tweets_arr.append(current_tweet)

            # Write to file every 1000 requests
            if len(loaded_tweets_arr) > 1000:
                print(f"Tweet threshold reached, appending {len(loaded_tweets_arr)} tweets to file {csv_file_name}!")
                append_to_csv(csv_file_name, loaded_tweets_arr)
                loaded_tweets_arr = []

            if req_remaining < 5:
                # if we almost the limit wait for 15 minutes
                print("No requests remaining, waiting for 15 minutes")
                time.sleep(15 * 60)
            else:
                print(f"Requests remaining: {req_remaining}")
                time.sleep(0.6 + random.random() * 0.2)

            # to get the next page of results
            tweet_diff = tmp_tweets_per_day - len(json_response["data"])
            if "next_token" in json_response["meta"] and tweet_diff > 0:
                tmp_tweets_per_day = 10 if tweet_diff < 10 else tweet_diff
                print(f"diff: {tweet_diff}, tmp_tweets_per_day: {tmp_tweets_per_day}")
                next_token = json_response["meta"]["next_token"]
            else:
                break

    print(f"\nFinished gathering tweets, appending {len(loaded_tweets_arr)} tweets to file {csv_file_name}!")
    append_to_csv(csv_file_name, loaded_tweets_arr)
    print(f"Finished collecting tweets in {time.time() - start_time:.2f} seconds")
