from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hey world, check out this source!"
