from flask import Flask, render_template, request, redirect, url_for, make_response
from handlers.auth import auth_handlers
from handlers.topic import topic_handlers
import uuid
from models.settings import db
from models.user import User
import hashlib
from models.topic import Topic
import os
import smartninja_redis
from handlers.comment import comment_handlers


redis = smartninja_redis.from_url(os.environ.get("REDIS_URL"))

app = Flask(__name__)
app.register_blueprint(auth_handlers)
app.register_blueprint(topic_handlers)
app.register_blueprint(comment_handlers)


db.create_all()


@app.route('/')
def index():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    topics = db.query(Topic).all()

    return render_template("index.html", user=user, topics=topics)


if __name__ == '__main__':
    app.run()