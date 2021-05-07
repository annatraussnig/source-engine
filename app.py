import json
import os

import twitter
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import nltk
nltk.download('averaged_perceptron_tagger')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from rake_nltk import Rake

load_dotenv()

api = twitter.Api(access_token_key=os.environ.get('TWITTER_ACCESS_TOKEN_KEY'),
                  access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'),
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
    if form.validate_on_submit():
        url = form.url.data
        find_original_tweet(url)
        analyze_timeline()
        message = "Looking for tweet source"
    return render_template('tweet.html', form=form, message=message)

def find_original_tweet(url):
    status_id = url.split('status/')[1].split('?')[0]
    status = json.loads(api.GetStatus(status_id).AsJsonString())
    # print(status)

def analyze_timeline():
    tweets = api.GetUserTimeline(screen_name="BarackObama")
    for tweet in tweets:
        text = tweet.full_text
        print(tweet.full_text)
        polarity = analyzer.polarity_scores(text)
        print(polarity)
        rake_nltk_var.extract_keywords_from_text(text)
        keyword_extracted = rake_nltk_var.get_ranked_phrases()[0:3]
        print(keyword_extracted)
        tokenized = nltk.word_tokenize(text)
        nouns = [word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)]
        print(nouns)
        print('\n\n')

# keep this as is
if __name__ == '__main__':
    app.run(debug=True)
