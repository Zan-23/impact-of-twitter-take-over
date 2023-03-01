import time

import detoxify
import pandas as pd
import torch
from sentence_splitter import split_text_into_sentences
from tqdm import tqdm
from unidecode import unidecode


def upgraded_generate_toxicity_for_tweet_file(model: detoxify.Detoxify, input_file: str, output_file: str):
    """
    This function gets the csv file with tweets (which should be lemmatized before), it then creates a new dataframe
    with headers and saves it to a file. Then it iterates over the tweets, splits them into sentences, gets the toxicity
    metrics for each sentence in a tweet and then averages them to get the toxicity metrics for the whole tweet.

    It saves the results periodically in the csv file and clears the current DataFrame to save memory. If it encounters
    any weird symbols when splitting up text it will convert it to unicode and try again. The toxicity metrics are saved
    to the output file which was given, and preserve order of the tweets.

    :param model: detoxify.Detoxify. Model to use for toxicity metrics (we used Detoxify('original', device="cuda"))
    :param input_file: String. Name of the csv file with tweets (should be lemmatized before).
    :param output_file: String. Name of the csv file to save the toxicity metrics to.
    """
    print(f"\nStarted generating toxicity metrics for:\n"
          f"-input file: '{input_file}',\n"
          f"-output file: '{output_file}'")
    tweets_df = pd.read_csv("./data/lemmatized/" + input_file)
    total_len = len(tweets_df.index)
    tweets_df = tweets_df[tweets_df["lang"] == "en"]
    print(f"Removed {total_len - len(tweets_df.index)} tweets out of {len(tweets_df.index)}, "
          f"since they were not in English")

    # if we don't do it, the toxicity metrics will missmatch down the line
    tweets_df = tweets_df.reset_index(drop=True)
    print("Tweet df:")
    print(tweets_df.head(5))

    # generating toxicity scores for each tweet
    start_time = time.time()
    csv_columns = list(tweets_df.columns) + ["toxicity", "severe_toxicity", "obscene", "threat", "insult",
                                             "identity_attack"]
    toxicity_df = pd.DataFrame(columns=csv_columns)
    # save headers to file
    toxicity_df.to_csv(output_file)
    # changed this column for lemmatized info
    content_list_p = tweets_df["processed_text"].to_list()
    content_list_raw = tweets_df["text"].to_list()

    # easiest to implement per text
    step = 1
    for i in tqdm(range(0, len(tweets_df.index), step)):
        if i % 5000 == 0 and i != 0:
            torch.cuda.empty_cache()
            toxicity_df.to_csv(output_file, mode='a', header=False)
            # print("At row: {i}. Cleared GPU cache and saved to file")
            toxicity_df = pd.DataFrame(columns=csv_columns)

        sentences_arr = []
        try:
            # before predicting, split text into sentences
            sentences_arr = split_text_into_sentences(text=content_list_p[i], language='en')
        except TypeError as e:
            # for handling bad string regex etc.
            print(f"At row {i}, encountered non-sentence splittable string '{content_list_p[i]}'")
            print(f"Trying to split the original sentence parsed with unidecode '{unidecode(content_list_raw[i])}'!")
            sentences_arr = split_text_into_sentences(text=unidecode(content_list_raw[i]), language='en')

        text_tox_arr = []
        for sentence in sentences_arr:
            curr_tox_dict = model.predict(sentence)
            text_tox_arr.append(curr_tox_dict)

        curr_tox_dict = {}
        # merge all sentence toxicities and take average (we could also take max)
        sentence_count = len(text_tox_arr)
        for key in text_tox_arr[0].keys():
            curr_tox_dict[key] = sum(tmp_dict[key] for tmp_dict in text_tox_arr) / sentence_count

        curr_tweet_dict = tweets_df.iloc[i:i + step].reset_index(drop=True).to_dict(orient="list")
        # we have to wrap our dict in an array to be converted to df
        merged_tweet_tox = pd.merge(pd.DataFrame(curr_tweet_dict), pd.DataFrame([curr_tox_dict]),
                                    left_index=True, right_index=True)
        toxicity_df = pd.concat([toxicity_df, merged_tweet_tox], ignore_index=True)

    toxicity_df.to_csv(output_file, mode='a', header=False)
    print(f"Execution took: {time.time() - start_time:.2f} seconds")
    print(f"Finished saving to file '{output_file}'\n")


def generate_toxicity_for_tweet_file(model: detoxify.Detoxify, input_file: str, output_file: str):
    """
    This function is outdated please use: upgraded_generate_toxicity_for_tweet_file instead.

    This function gets the csv file with tweets (which should be lemmatized before), it then creates a new dataframe
    with headers and saves it to a file. Then it iterates over the tweets and gets the toxicity metrics for each tweet.

    It saves the results periodically in the csv file and clears the current DataFrame to save memory.
    The toxicity metrics are saved to the output file which was given, and preserve order of the tweets.

    :param model: detoxify.Detoxify. Model to use for toxicity metrics (we used Detoxify('original', device="cuda"))
    :param input_file: String. Name of the csv file with tweets (should be lemmatized before).
    :param output_file: String. Name of the csv file to save the toxicity metrics to.
    """
    print(f"\nStarted generating toxicity metrics for:\n"
          f"-input file: '{input_file}',\n"
          f"-output file: '{output_file}'")
    tweets_df = pd.read_csv("./data/raw_hashtags/" + input_file)
    total_len = len(tweets_df.index)
    tweets_df = tweets_df[tweets_df["lang"] == "en"]
    print(f"Removed {total_len - len(tweets_df.index)} tweets out of {len(tweets_df.index)}, "
          f"since they were not in English")

    # if we don't do it, the toxicity metrics will missmatch down the line
    tweets_df = tweets_df.reset_index(drop=True)
    print("Tweet df:")
    print(tweets_df.head(5))

    # generating toxicity scores for each tweet
    start_time = time.time()
    csv_columns = list(tweets_df.columns) + ["toxicity", "severe_toxicity", "obscene", "threat", "insult",
                                             "identity_attack"]
    toxicity_df = pd.DataFrame(columns=csv_columns)
    # save headers to file
    toxicity_df.to_csv(output_file)
    content_list = tweets_df["text"].to_list()

    # multistep - it should work fine now! You can use it and it should be a bit faster
    step = 50
    for i in tqdm(range(0, len(tweets_df.index), step)):
        if i % 500 == 0 and i != 0:
            # print(f"At row: {i}")
            torch.cuda.empty_cache()
            toxicity_df.to_csv(output_file, mode='a', header=False)
            # print("Cleared GPU cache and saved to file")
            toxicity_df = pd.DataFrame(columns=csv_columns)

        curr_tox_dict = model.predict(content_list[i:i + step])
        curr_tweet_dict = tweets_df.iloc[i:i + step].reset_index(drop=True).to_dict(orient="list")
        merged_tweet_tox = pd.merge(pd.DataFrame(curr_tweet_dict), pd.DataFrame(curr_tox_dict),
                                    left_index=True, right_index=True)
        toxicity_df = pd.concat([toxicity_df, merged_tweet_tox], ignore_index=True)

    toxicity_df.to_csv(output_file, mode='a', header=False)
    print(f"Execution took: {time.time() - start_time:.2f} seconds")
    print(f"Finished saving to file '{output_file}'\n")