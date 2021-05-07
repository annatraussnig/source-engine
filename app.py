import json
import os

import twitter
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

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


class TweetForm(FlaskForm):
    url = StringField('Tweet Url:', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TweetForm()
    message = ""
    if form.validate_on_submit():
        url = form.url.data
        original_tweet_user_id = find_original_tweet_user_id(url)
        print(original_tweet_user_id)
        message = "Looking for tweet source"
    return render_template('tweet.html', form=form, message=message)


def find_original_tweet_user_id(url):
    status_id = url.split('status/')[1].split('?')[0]
    status = json.loads(api.GetStatus(status_id).AsJsonString())

    hashtag_string = ' AND '.join([f'%23{hashtag["text"]}' for hashtag in status['hashtags']])
    result = api.GetSearch(
        raw_query=f"q={hashtag_string}&count=200", return_json=True)['statuses']

    print(result)

    while len(result) == 200:
        result = api.GetSearch(raw_query=f"q={hashtag_string}&count=200&max_id={result[-1]['id']}", return_json=True)[
            'statuses']

    if not result:
        original_tweet = status
    else:
        original_tweet = json.loads(api.GetStatus(result[-1]['id']).AsJsonString())

    return original_tweet['user']['id']


# keep this as is
if __name__ == '__main__':
    app.run(debug=True)
