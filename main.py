from flask import Flask, render_template, request, redirect, url_for, make_response
import uuid
from models.settings import db
from models.user import User
import hashlib
from models.topic import Topic
import os
import smartninja_redis

redis = smartninja_redis.from_url(os.environ.get("REDIS_URL"))

app = Flask(__name__)
db.create_all()


@app.route('/')
def index():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    topics = db.query(Topic).all()

    return render_template("index.html", user=user, topics=topics)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        repeat = request.form.get("repeat")

        if password != repeat:
            return "Passwords do not match! Try again.."

        user = User(username=username, password_hash=hashlib.sha256(password.encode()).hexdigest(), session_token=str(uuid.uuid4()))

        db.add(user)
        db.commit()

        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", user.session_token, httponly=True, samesite="Strict")

        return response


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = db.query(User).filter_by(username=username).first()
        if not user:
            return "This user doesn't exist."
        else:
            if password_hash == user.password_hash:
                user.session_token = str(uuid.uuid4())
                db.add(user)
                db.commit()

                response = make_response(redirect(url_for("index")))
                response.set_cookie("session_token", user.session_token, httponly=True, samesite='Strict')

                return response
            else:
                return "Your password is incorrect."


"""@app.route('/create_topic', methods=["GET", "POST"])
def topic_create():
    if request.method == "GET":
        return render_template("topic_create.html")

    elif request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")

        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

    if not user:
        return redirect(url_for('login'))

    topic = Topic.create(title=title, text=text, author=user)

    return redirect(url_for('index'))"""


@app.route("/create_topic", methods=["GET", "POST"])
def topic_create():
    # get current user (author)
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    # only logged in users can create a topic
    if not user:
        return redirect(url_for('login'))

    # GET method
    if request.method == "GET":
        csrf_token = str(uuid.uuid4())  # create CSRF token

        redis.set(name=csrf_token, value=user.username)  # store CSRF token into Redis for that specific user
        return render_template("topic_create.html", user=user, csrf_token=csrf_token)

    # POST method
    elif request.method == "POST":
        csrf = request.form.get("csrf")  # csrf from HTML
        redis_csrf_username = redis.get(name=csrf).decode()  # username value stored under the csrf name from redis

        if redis_csrf_username and redis_csrf_username == user.username:  # if they match, allow user to create a topic
            title = request.form.get("title")
            text = request.form.get("text")

            # create a Topic object
            topic = Topic.create(title=title, text=text, author=user)

            return redirect(url_for('index'))
        else:
            return "CSRF token is not valid!"


@app.route("/topic/<topic_id>", methods=["GET"])
def topic_details(topic_id):
    topic = db.query(Topic).get(int(topic_id))
    # get current user (author)
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    return render_template("topic_details.html", topic=topic, user=user)


@app.route("/topic/<topic_id>/edit", methods=["GET", "POST"])
def topic_edit(topic_id):
    topic = db.query(Topic).get(int(topic_id))

    if request.method == "GET":
        return render_template("topic_edit.html", topic=topic)
    elif request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")

        # get current user (author)
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

        # check if user is logged in and user is author
        if not user:
            return redirect(url_for('login'))
        elif topic.author.id != user.id:
            return "You are not the author!"
        else:
            # update the topic fields
            topic.title = title
            topic.text = text
            db.add(topic)
            db.commit()

            return redirect(url_for('topic_details', topic_id=topic_id))


@app.route("/topic/<topic_id>/delete", methods=["GET", "POST"])
def topic_delete(topic_id):
    topic = db.query(Topic).get(int(topic_id))  # get topic from db by ID

    if request.method == "GET":
        return render_template("topic_delete.html", topic=topic)

    elif request.method == "POST":
        # get current user (author)
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

        # check if user is logged in and user is author
        if not user:
            return redirect(url_for('login'))
        elif topic.author_id != user.id:
            return "You are not the author!"
        else:  # if user IS logged in and current user IS author
            # delete topic
            db.delete(topic)
            db.commit()
            return redirect(url_for('index'))



if __name__ == '__main__':
    app.run()