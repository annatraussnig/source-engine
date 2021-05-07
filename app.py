import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

load_dotenv()

app = Flask(__name__)

# Flask-WTF requires an encryption key - the string can be anything
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# load twitter api key from .env
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')

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
        message = "Looking for tweet source"
    return render_template('tweet.html', form=form, message=message)


# keep this as is
if __name__ == '__main__':
    app.run(debug=True)
