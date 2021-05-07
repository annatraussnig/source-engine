import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import twitter

load_dotenv()

api = twitter.Api(access_token_key=os.environ.get('TWITTER_ACCESS_TOKEN_KEY'),
                  access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'))

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
    results = api.GetSearch(
        raw_query="q=twitter%20&result_type=recent&since=2021-04-06&count=10")
    print(results)
    form = TweetForm()
    message = ""
    if form.validate_on_submit():
        url = form.url.data
        message = "Looking for tweet source"
    return render_template('tweet.html', form=form, message=message)


# keep this as is
if __name__ == '__main__':
    app.run(debug=True)
