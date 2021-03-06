import json
import os
import sys
from datetime import datetime

import twitter
import requests
import urllib.parse
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from urllib.parse import urlparse
from nltk.corpus import stopwords
from unicodedata import category

import nltk

nltk.download('averaged_perceptron_tagger')
nltk.download('vader_lexicon')

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from rake_nltk import Rake

load_dotenv()

api = twitter.Api(access_token_key=os.environ.get('TWITTER_ACCESS_TOKEN_KEY'),
                  access_token_secret=os.environ.get(
                      'TWITTER_ACCESS_TOKEN_SECRET'),
                  consumer_key=os.environ.get('TWITTER_CONSUMER_KEY'),
                  consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET'),
                  tweet_mode='extended'
                  )

app = Flask(__name__)

# Flask-WTF requires an encryption key - the string can be anything
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Flask-Bootstrap requires this line
Bootstrap(app)

analyzer = SentimentIntensityAnalyzer()
rake_nltk_var = Rake()
is_noun = lambda pos: pos[:2] == 'NN'


class TweetForm(FlaskForm):
    url = StringField('Tweet Url:', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TweetForm()
    message = ""
    searched_tweet_html = ""
    original_tweet_html = ""
    timeline_data = ""
    if form.validate_on_submit():
        url = form.url.data
        searched_tweet_html = get_inline_html_for_tweet(url)
        original_tweet = find_original_tweet(url)
        if original_tweet:
            original_tweet_html = get_inline_html_for_tweet('https://twitter.com/blank/status/' + original_tweet[
                'id_str'])  # the URL construction is hacky but seems to work
            timeline_data = analyze_timeline(original_tweet['user']['id'])
            print(timeline_data)
        else:
            original_tweet_html = '<p>At the moment we only analyze tweets with hashtags or links</p>'
        message = "Looking for tweet source"
    return render_template('tweet.html', form=form, message=message, searched_tweet=searched_tweet_html,
                           original_tweet=original_tweet_html, timeline_data=json.dumps(timeline_data))


def get_inline_html_for_tweet(url):
    response = requests.get('https://publish.twitter.com/oembed?url=' + url)
    if response:
        return response.json()['html']
    else:
        return '<p>Tweet not found</p>'


def find_original_tweet(url):
    status_id = url.split('status/')[1].split('?')[0]
    status = json.loads(api.GetStatus(status_id).AsJsonString())
    status = status['retweeted_status'] if 'retweeted_status' in status else status

    search_string = ""
    if status['hashtags']:
        search_string = ' AND '.join(
            [f'%23{hashtag["text"]}' for hashtag in status['hashtags']])
    elif status['urls']:
        search_string = ' AND '.join(
            [f'url%3A{urllib.parse.quote(url["expanded_url"], safe="")}' for url in status['urls']])
    else:
        return None

    result = get_sorted_tweet_list(f"q={search_string}&count=100&result_type=recent")
    while len(result) == 100:
        tweets = get_sorted_tweet_list(f"q={search_string}&count=100&result_type=recent&max_id={result[-1]['id']}")
        if not tweets:
            break
        else:
            result = tweets

    if not result:
        original_tweet = status
    else:
        original_tweet = json.loads(
            api.GetStatus(result[-1]['id']).AsJsonString())
    return original_tweet


# user_id default to Barack Obama for testing
def analyze_timeline(user_id=813286):
    user = api.GetUser(user_id=user_id, return_json=True)
    # we restrict ourselves to the last 1000 tweets for api rate limiting reasons
    tweets = api.GetUserTimeline(user_id=user_id, count=200)
    for i in range(4):
        res = api.GetUserTimeline(user_id=user_id, count=200, max_id=tweets[-1].id)
        if res:
            tweets += res
        else:
            break

    words = []
    for tweet in tweets:
        text = tweet.full_text
        polarity = analyzer.polarity_scores(text)
        rake_nltk_var.extract_keywords_from_text(text)
        keyword_extracted = rake_nltk_var.get_ranked_phrases()[0:3]
        tokenized = nltk.word_tokenize(text)
        nouns = [word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)]
        for noun in nouns:
            found = False
            for word in words:
                if word['word'] == noun:
                    word['count'] += 1
                    word['avg_tweet_sentiment'] = ((word['count'] - 1) * word['avg_tweet_sentiment'] + polarity[
                        'compound']) / word['count']
                    found = True
            if not found:
                words.append({
                    'word': noun,
                    'count': 1,
                    'avg_tweet_sentiment': polarity['compound']
                })
    # Filter list for stopwords and punctuation
    stop_words = set(stopwords.words())
    codepoints = range(sys.maxunicode + 1)
    chrs = (chr(i) for i in range(sys.maxunicode + 1))
    punctuation = set(c for c in chrs if category(c).startswith("P"))
    stop_words = stop_words.union(punctuation)
    stop_words = stop_words.union(['https', '@', '???', 's', '%', '-', '???'])
    words = [word for word in words if word['word'].lower() not in stop_words]
    words = sorted(words, key=lambda k: k['count'], reverse=True)[:50]
    return {
        'name': user['name'],
        'description': user['description'],
        'profile_image_url': user['profile_image_url'],
        'words': words,
    }


def created_at_to_date(created_at):
    date = datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    return date


def flatten_retweets(tweet_list):
    return [tweet['retweeted_status'] if 'retweeted_status' in tweet else tweet for tweet in tweet_list]


def get_sorted_tweet_list(query):
    result = api.GetSearch(raw_query=query, result_type='recent', return_json=True)['statuses']
    result = flatten_retweets(result)
    result.sort(key=lambda k: created_at_to_date(k['created_at']), reverse=True)
    return result


# keep this as is
if __name__ == '__main__':
    app.run(debug=True)
