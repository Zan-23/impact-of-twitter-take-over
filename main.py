
from src.twitter_download_functions import download_tweets, partition_day_by_tweets

if __name__ == "__main__":
    download_tweets(tweets_per_day=6000, start_time="01/06/2022 00:00", end_time="28/12/2022 00:00")
    # partition_day_by_tweets(1500, "01/06/2022 00:00", "03/06/2022 00:00")
