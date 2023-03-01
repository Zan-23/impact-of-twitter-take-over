import time

import numpy as np
import pandas as pd
import spacy
from tqdm import tqdm


def optimized_prepare_text_for_tweet_file(replace_symbols_regex, input_file: str, output_file_name: str,
                                          nlp_model: spacy.Language):
    """
    Function is optimized for speed and memory usage. It loads the data, replaces the unknown symbols which match
    the regex, feeds each tweet to the spacy model and saves the results to a file.

    :param replace_symbols_regex: re.compile object which matches the symbols to be replaced
    :param input_file: String. Name of the file to be lemmatized.
    :param output_file_name: String. Name of the output file.
    :param nlp_model: spacy.Language object. The model to be used for lemmatization (used spacy.load('en_core_web_sm'))
    """
    print(f"\nStarted generating toxicity metrics for:\n"
          f"-input file: '{input_file}',\n"
          f"-output file: '{output_file_name}'")
    start_time = time.time()
    tweets_df = pd.read_csv("./data/raw_hashtags/" + input_file)
    total_len = len(tweets_df.index)

    tweets_df = tweets_df[tweets_df["lang"] == "en"]
    print(
        f"Removed {total_len - len(tweets_df.index)} tweets out of {len(tweets_df.index)}, since they were not in English\n")
    # if we don't do it, the toxicity metrics will missmatch down the line
    tweets_df = tweets_df.reset_index(drop=True)

    # removed emoji and other weird symbols
    symbol_removed_col = tweets_df["text"].str.replace(replace_symbols_regex, "")
    # remove new lines, tabs, and multiple spaces.
    symbol_removed_col = symbol_removed_col.str.replace(r'\r+|\n+|\t+', '', regex=True).replace(r'\s+', ' ', regex=True)

    lemmas_arr = []
    # perform multi-threaded execution
    for doc in tqdm(nlp_model.pipe(symbol_removed_col.astype("unicode").values, batch_size=15, n_process=3)):
        if doc.has_annotation:
            # contains the lemmatized sentence
            lemmas_arr.append(" ".join([token.lemma_ for token in doc]))
        else:
            # We want to make sure that the lists of parsed results have the
            # same number of entries of the original Dataframe, so add some blanks in case the parse fails
            lemmas_arr.append("")

    tweets_df['processed_text'] = pd.Series(lemmas_arr)
    print("Finished lemmitization")

    tweets_df.to_csv(output_file_name, header=True)
    print(f"\nExecution took: {time.time() - start_time:.2f} seconds")
    print(f"Finished saving to file '{output_file_name}'\n")


def prepare_text_for_tweet_file(replace_symbols_regex, input_file: str, output_file_name: str,
                                nlp_model: spacy.Language):
    """
    Outdated, is slow compared to optimized_prepare_text_for_tweet_file.
    Function is optimized for speed and memory usage. It loads the data, replaces the unknown symbols which match
    the regex, feeds each tweet to the spacy model and saves the results to a file.

    :param replace_symbols_regex: re.compile object which matches the symbols to be replaced
    :param input_file: String. Name of the file to be lemmatized.
    :param output_file_name: String. Name of the output file.
    :param nlp_model: spacy.Language object. The model to be used for lemmatization (used spacy.load('en_core_web_sm'))
    """
    print(f"\nStarted generating toxicity metrics for:\n"
          f"-input file: '{input_file}',\n"
          f"-output file: '{output_file_name}'")
    start_time = time.time()
    tweets_df = pd.read_csv("./data/raw_hashtags/" + input_file)
    total_len = len(tweets_df.index)

    tweets_df = tweets_df[tweets_df["lang"] == "en"]
    print(
        f"Removed {total_len - len(tweets_df.index)} tweets out of {len(tweets_df.index)}, since they were not in English\n")
    # if we don't do it, the toxicity metrics will missmatch down the line
    tweets_df = tweets_df.reset_index(drop=True)

    # add new column for processed text
    tweets_df["text_processed"] = np.nan
    preprocessed_text_arr = []
    for index, row in tweets_df.iterrows():
        if index % 500 == 0:
            print(f"At row: {index}/{len(tweets_df.index)}")
        # remove emojis
        text = replace_symbols_regex.sub(r'', row["text"])
        # lematize it using spacy
        lemmas = ' '.join([x.lemma_ for x in nlp_model(text)])

        # add it to the array which will be added as a column at the end
        preprocessed_text_arr.append(lemmas)

    tweets_df["text_processed"] = pd.Series(preprocessed_text_arr)
    print("Finished lemmitization")

    tweets_df.to_csv(output_file_name, header=True)
    print(f"\nExecution took: {time.time() - start_time:.2f} seconds")
    print(f"Finished saving to file '{output_file_name}'\n")
    return tweets_df
