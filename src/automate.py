import pandas as pd # type: ignore
import nltk
nltk.download('vader_lexicon')

import tweepy
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import defaultdict

# Setup Twitter API credentials (replace with your own credentials)
meta_data = []
stories = []
text_ids = []
dates = []

en_stop = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as',
           'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot',
           'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each',
           'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd",
           "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd",
           "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more',
           'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought',
           'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should',
           "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then',
           'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to',
           'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't",
           'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's",
           'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself',
           'yourselves', 'apos', 's', 'I', 'will', 'go', 'get', '(', ')', '?', ':', ';', ',', '.', '!', '/', '"', "'", "...",
           "``", "&apos", "&apos;s", "&apos;&apos;", "-lsb-", "-rsb-", "-lcb-", "-rcb-", "-lrb-", "-rrb-", "O&apos;MALLEY", "--"]

# Initialize tweepy API
auth = tweepy.OAuth1UserHandler(meta_data,stories,text_ids,dates,en_stop)
api = tweepy.API(auth)

# Function to fetch tweets using a keyword
def fetch_tweets(keyword, count=100):
    tweets = []
    for tweet in tweepy.Cursor(api.search_tweets, q=keyword, lang="en", tweet_mode='extended').items(count):
        if not tweet.retweeted and 'RT @' not in tweet.full_text:  # Filter retweets
            tweets.append(tweet.full_text)
    return tweets

# Function for sentiment analysis
def analyze_sentiments(tweets):
    sid = SentimentIntensityAnalyzer()
    sentiment_data = defaultdict(list)  # stores categorized tweets
    
    for tweet in tweets:
        sentiment_scores = sid.polarity_scores(tweet)
        sentiment = "neutral"
        if sentiment_scores['compound'] >= 0.05:
            sentiment = "positive"
        elif sentiment_scores['compound'] <= -0.05:
            sentiment = "negative"
        
        sentiment_data[sentiment].append(tweet)
    
    return sentiment_data

# Function to detect controversy
def detect_controversy(sentiment_data):
    total_tweets = sum([len(sentiment_data[sent]) for sent in sentiment_data])
    
    if total_tweets == 0:
        return "Not enough data"
    
    positive_ratio = len(sentiment_data['positive']) / total_tweets
    negative_ratio = len(sentiment_data['negative']) / total_tweets
    
    # Heuristic for controversy: balanced positive/negative ratios
    if 0.3 <= positive_ratio <= 0.7 and 0.3 <= negative_ratio <= 0.7:
        return f"Controversial content detected! Positive: {positive_ratio*100:.2f}%, Negative: {negative_ratio*100:.2f}%"
    else:
        return f"Non-controversial content. Positive: {positive_ratio*100:.2f}%, Negative: {negative_ratio*100:.2f}%"

# Main function to automate the controversy detection process
def main(keyword, tweet_count=100):
    print(f"Fetching tweets for keyword: {keyword}")
    tweets = fetch_tweets(keyword, count=tweet_count)
    
    print(f"Analyzing {len(tweets)} tweets for sentiment...")
    sentiment_data = analyze_sentiments(tweets)
    
    result = detect_controversy(sentiment_data)
    print(result)

# Example usage
if __name__ == "__main__":
    main(keyword="climate change", tweet_count=200)
