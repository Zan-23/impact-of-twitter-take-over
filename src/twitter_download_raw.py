import csv
import datetime
import random
import time

import pandas as pd
import requests

from src.twitter_downloader import get_bearer_token, partition_tweets_by_days, extract_information_from_tweet


def get_api_url():
    # endpoint for all tweets, not just recent ones
    search_url = "https://api.twitter.com/2/tweets/search/all"
    return search_url


def connect_to_endpoint(url, headers, params, next_token=None):
    # next token is given from request if there are more available tweets
    params['next_token'] = next_token
    response = requests.request("GET", url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)

    request_remaining = int(response.headers["x-rate-limit-remaining"])
    response_code = response.status_code

    return response.json(), request_remaining


def prepare_parameter_json(query, max_results, start_time, end_time):
    # time has to be in RFC 3339 format
    # no spaces between words in fields!
    params = {"query": query,
              "max_results": max_results,
              "start_time": start_time.isoformat() + "Z",
              "end_time": end_time.isoformat() + "Z",
              "expansions": "author_id,in_reply_to_user_id,geo.place_id",
              "tweet.fields": "id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,lang,"
                              "public_metrics,referenced_tweets,reply_settings,source",
              "user.fields": "id,name,username,created_at,description,public_metrics,verified",
              "place.fields": "full_name,id,country,country_code,geo,name,place_type",
              "next_token": {}
              }
    return params


def create_csv_file():
    curr_date = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
    column_names = ["tweet_id", "lang", "author_id", "created_at", "source", "text", "geo", "retweet_count",
                    "reply_count", "like_count", "quote_count"]
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


def main_direct_req(total_amount_of_tweets=30):
    """
    Info for building queries: https://developer.twitter.com/en/docs/twitter-api/tweets/counts/integrate/build-a-query
    Status codes https://developer.twitter.com/en/docs/twitter-api/rate-limits#headers-and-codes

    :param total_amount_of_tweets:
    :return:
    """
    bearer_token = get_bearer_token()
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    search_query = "Elon musk lang:en place_country:US -is:reply -is:retweet -is:quote"
    # -is:reply -is:retweet -is:quote -> ensures we only get original tweets
    start_date = datetime.datetime.strptime("01/06/2022 00:00", "%d/%m/%Y %H:%M")
    end_date = datetime.datetime.strptime("03/06/2022 00:00", "%d/%m/%Y %H:%M")
    print(f"Started search for tweet query '{search_query}' in date range: {start_date} -> {end_date}")

    tweets_per_day, date_ranges = partition_tweets_by_days(total_amount_of_tweets=total_amount_of_tweets,
                                                           start_time=start_date, end_time=end_date)

    loaded_tweets_arr = []
    csv_file_name = create_csv_file()
    start_time = time.time()
    next_token = None
    for start_time_i, end_time_i in date_ranges:
        print(f"\nCollecting '{tweets_per_day}' tweets for date range: {start_time_i} -> {end_time_i}")
        query_params = prepare_parameter_json(query=search_query, max_results=tweets_per_day,
                                              start_time=start_time_i, end_time=end_time_i)

        new_url = get_api_url()
        json_response, req_remaining = connect_to_endpoint(new_url, headers, query_params, next_token)

        for i, tweet in enumerate(json_response["data"]):
            current_tweet = extract_information_from_tweet(tweet)
            loaded_tweets_arr.append(current_tweet)

        # Write to file every 1000 requests
        if len(loaded_tweets_arr) > 1000:
            print(f"Tweet threshold reached, appending {len(loaded_tweets_arr)} tweets to file {csv_file_name}!")
            print("Elements in array: ", len(loaded_tweets_arr[0]))
            append_to_csv(csv_file_name, loaded_tweets_arr)
            loaded_tweets_arr = []

        if req_remaining < 5:
            # if we almost the limit wait for 15 minutes
            print("No requests remaining, waiting for 15 minutes")
            time.sleep(15 * 60)
        else:
            print(f"Requests remaining: {req_remaining}")
            time.sleep(0.5 + random.random())

    print(f"\nFinished gathering tweets, appending {len(loaded_tweets_arr)} tweets to file {csv_file_name}!")
    append_to_csv(csv_file_name, loaded_tweets_arr)
    print(f"Finished collecting tweets in {time.time() - start_time} seconds")

    # if "next_token" in json_response["meta"]:
    #     # Save the token to use for next call
    #     next_token = json_response["meta"]["next_token"]
    #     print("Using next token: ", next_token)
    #     # don't increment and get the next page
    # else:
    #     date_range_index += 1
    #     print("No more tokens. Next date range index: ", date_range_index)
    #
    #     # Since this is the final request, turn flag to false to move to the next time period.
    #     next_token = None
