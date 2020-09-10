from flask import render_template, request, redirect, url_for, make_response, Blueprint
import uuid
from models.topic import Topic
from models.settings import db
from models.user import User
from utils.redis_helper import create_csrf_token, validate_csrf
from models.comment import Comment
topic_handlers = Blueprint("topic", __name__)

@topic_handlers.route('/')
def index():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    topics = db.query(Topic).all()

    return render_template("topic/index.html", user=user, topics=topics)


"""@app.route('/create_topic', methods=["GET", "POST"])
def topic_create():
    if request.method == "GET":
        return render_template("topic/topic_create.html")

    elif request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")

        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

    if not user:
        return redirect(url_for('login'))

    topic = Topic.create(title=title, text=text, author=user)

    return redirect(url_for('topic.index'))"""


@topic_handlers.route("/create_topic", methods=["GET", "POST"])
def topic_create():
    # get current user (author)
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    # only logged in users can create a topic
    if not user:
        return redirect(url_for('auth.login'))

    # GET method
    if request.method == "GET":
        """csrf_token = str(uuid.uuid4())  # create CSRF token
        redis.set(name=csrf_token, value=user.username)  # store CSRF token into Redis for that specific user"""

        csrf_token = create_csrf_token(user.username)
        return render_template("/topic/topic_create.html", user=user, csrf_token=csrf_token)

    # POST method
    elif request.method == "POST":
        csrf = request.form.get("csrf")  # csrf from HTML
        """redis_csrf_username = redis.get(name=csrf).decode()  # username value stored under the csrf name from redis"""

        if validate_csrf(csrf, user.username):
            title = request.form.get("title")
            text = request.form.get("text")

            # create a Topic object
            topic = Topic.create(title=title, text=text, author=user)

            return redirect(url_for('topic.index'))
        else:
            return "CSRF token is not valid!"


@topic_handlers.route("/topic/<topic_id>", methods=["GET"])
def topic_details(topic_id):
    topic = db.query(Topic).get(int(topic_id))
    # get current user (author)
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    # get comments for this topic
    comments = db.query(Comment).filter_by(topic=topic).all()

    # START test background tasks (TODO: delete this code later)
    if os.getenv('REDIS_URL'):
        from tasks import get_random_num
        get_random_num()
    # END test background tasks

    return render_template("topic/topic_details.html", topic=topic, user=user,
                           csrf_token=create_csrf_token(user.username), comments=comments)


@topic_handlers.route("/topic/<topic_id>/edit", methods=["GET", "POST"])
def topic_edit(topic_id):
    topic = db.query(Topic).get(int(topic_id))

    if request.method == "GET":
        return render_template("topic/topic_edit.html", topic=topic)
    elif request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")

        # get current user (author)
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

        # check if user is logged in and user is author
        if not user:
            return redirect(url_for('auth.login'))
        elif topic.author.id != user.id:
            return "You are not the author!"
        else:
            # update the topic fields
            topic.title = title
            topic.text = text
            db.add(topic)
            db.commit()

            return redirect(url_for('topic.topic_details', topic_id=topic_id))


@topic_handlers.route("/topic/<topic_id>/delete", methods=["GET", "POST"])
def topic_delete(topic_id):
    topic = db.query(Topic).get(int(topic_id))  # get topic from db by ID

    if request.method == "GET":
        return render_template("topic/topic_delete.html", topic=topic)

    elif request.method == "POST":
        # get current user (author)
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

        # check if user is logged in and user is author
        if not user:
            return redirect(url_for('auth.login'))
        elif topic.author_id != user.id:
            return "You are not the author!"
        else:  # if user IS logged in and current user IS author
            # delete topic
            db.delete(topic)
            db.commit()
            return redirect(url_for('topic.index'))
