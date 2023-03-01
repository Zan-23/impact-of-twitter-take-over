
from src.twitter_download_functions import download_tweets, partition_day_by_tweets

if __name__ == "__main__":
    search_query = "( trump OR #trump OR @trump ) lang:en -is:retweet -is:quote -has:links -is:reply"
    #  last execution of this code took 31061.31 seconds
    download_tweets(search_query=search_query,
                    tweets_per_day=18000,
                    start_time="01/06/2022 00:00",
                    end_time="03/01/2023 00:00")
    # partition_day_by_tweets(1500, "01/06/2022 00:00", "03/06/2022 00:00")
