import datetime
import pickle
import random

import numpy as np
import oauthlib
from tensorflow.keras.models import load_model

# SETUP THE WEB PAGE
import os
import pathlib
import warnings
import json
import nltk
import requests
import google.auth.transport.requests
import email_validator
import bcrypt
# nltk.download('popular')
from nltk.stem import WordNetLemmatizer

from flask import Flask, render_template, request, session, abort, redirect
from flask_socketio import SocketIO, join_room, emit
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin

from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol

server = Flask(__name__)
server.debug = True
server.static_folder = 'static'
server.config['SECRET_KEY'] = 'ntcmm7xqp2ujkjr'
server.config['SESSION_TYPE'] = 'filesystem'
server.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
server.config['SECURITY_PASSWORD_SALT'] = 'd8a774a3mi0oy8d'
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
server.config["MAIL_MAX_EMAILS"] = 30
server.config['MAIL_USE_TLS'] = False
server.config['MAIL_USE_SSL'] = True
socket_ = SocketIO(server, cors_allowed_origins='*', manage_session=True)

# CREATE THE DATABASE
# server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_log.sqlite3'
server.config['SQLALCHEMY_BINDS'] = {
    'all_chats': 'sqlite:///db/chat_log.sqlite3',
    'to_login': 'sqlite:///db/admin_account.sqlite3',
    'to_notify': 'sqlite:///db/contacts.sqlite3',
    'logged_in': 'sqlite:///db/logged_users.sqlite3'
}
db = SQLAlchemy(server)
db.init_app(server)
db.create_all(
    bind=['all_chats', 'to_login', 'to_notify', 'logged_in'])
# SETTING UP THE MAIL OF BOT
mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'makibotmail@gmail.com',
    "MAIL_PASSWORD": 'P@$$W012DF012M@K1130T'
}

server.config.update(mail_settings)
mail = Mail(server)
# accuracy of maki bot set to 0 as default
acc = 0

admin_role_users = db.Table('admin_role_users',
                            db.Column('admin_id', db.Integer, db.ForeignKey('admin_login.id')),
                            db.Column('admin_role_id', db.Integer, db.ForeignKey('admin_role.id')))
contact_role_users = db.Table('contact_role_users',
                              db.Column('contact_id', db.Integer, db.ForeignKey('contacts.id'), primary_key=True),
                              db.Column('contact_role_id', db.Integer, db.ForeignKey('contact_role.id')))
logged_role_users = db.Table('logged_role_users',
                             db.Column('logged_id', db.Integer, db.ForeignKey('logged_in_users.id'), primary_key=True),
                             db.Column('logged_role_id', db.Integer, db.ForeignKey('logged_role.id')))
chat_role_users = db.Table('chat_role_users',
                           db.Column('chat_id', db.Integer, db.ForeignKey('chat_log.id'), primary_key=True),
                           db.Column('chat_role_id', db.Integer, db.ForeignKey('chat_role.id')))


class LoggedInUsers(db.Model):
    __bind_key__ = 'logged_in'
    id = db.Column('id', db.Integer, primary_key=True)
    log_user_name = db.Column('username', db.String(70))
    log_user_email = db.Column('email', db.String(70))
    active = db.Column(db.Boolean())
    roles = db.relationship(
        'LoggedRole',
        secondary=logged_role_users,
        backref=db.backref('LoggedInUsers', lazy='dynamic')
    )


class LoggedRole(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))
    key = db.relationship(
        'LoggedRole',
        secondary=logged_role_users,
        backref=db.backref('logged_role', lazy='dynamic')
    )


class ChatLog(db.Model):
    __bind_key__ = 'all_chats'
    id = db.Column('id', db.Integer, primary_key=True)
    message = db.Column('message', db.String(600))
    timestamp = db.Column('timestamp', db.String(100))
    msg_from = db.Column('msg_from', db.String(100))
    msg_session = db.Column('msg_session', db.String(100))
    user_role = db.Column('user_role', db.String(50))
    active = db.Column(db.Boolean(), default=0)
    roles = db.relationship(
        'ChatRole',
        secondary=chat_role_users,
        backref=db.backref('chat_log', lazy='dynamic')
    )


class ChatRole(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))
    key = db.relationship(
        'ChatRole',
        secondary=chat_role_users,
        backref=db.backref('chat_role', lazy='dynamic')
    )


# ADMINS THAT CAN MANAGE DATABASE AND CHAT WITH APPLICANTS
class AdminLogin(db.Model, UserMixin):
    __bind_key__ = 'to_login'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100))
    middle = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    email = db.Column(db.String(80), unique=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship(
        'AdminRole',
        secondary=admin_role_users,
        backref=db.backref('AdminLogin', lazy='dynamic')
    )


class AdminRole(db.Model, RoleMixin):
    __tablename__ = "admin_role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))
    key = db.relationship(
        'AdminRole',
        secondary=admin_role_users,
        backref=db.backref('admin_role', lazy='dynamic')
    )


# CONTACT IS PERSONNEL THAT CANNOT CRUD BUT CAN ONLY CHAT WITH APPLICANTS
class Contacts(db.Model, UserMixin):
    __bind_key__ = 'to_notify'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100))
    middle = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    email = db.Column(db.String(80), unique=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship(
        'ContactRole',
        secondary=contact_role_users,
        backref=db.backref('contacts', lazy='dynamic')
    )


class ContactRole(db.Model, RoleMixin):
    __tablename__ = "contact_role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))
    key = db.relationship(
        'ContactRole',
        secondary=contact_role_users,
        backref=db.backref('contact_role', lazy='dynamic')
    )


logged_datastore = SQLAlchemyUserDatastore(db, LoggedInUsers, LoggedRole)
chat_datastore = SQLAlchemyUserDatastore(db, ChatLog, ChatRole)
contact_datastore = SQLAlchemyUserDatastore(db, Contacts, ContactRole)
admin_datastore = SQLAlchemyUserDatastore(db, AdminLogin, AdminRole)

dialogs = json.loads(open('dialogs.json').read())
words = pickle.load(open('texts.pkl', 'rb'))
classes = pickle.load(open('labels.pkl', 'rb'))

lemmatizer = WordNetLemmatizer()
model = load_model('model.h5')
warnings.filterwarnings("ignore")


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("[Found] in bag: %s" % w)
    return np.array(bag)


def predict_class(sentence, model):
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25

    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"dialog": classes[r[0]], "probability": str(r[1])})
        global acc
        acc = r[1]
    return return_list


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "580038653504-dufja2o5sm0m3r1ro6etk6p4uqn9onag.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_auth.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


# prevent unauthorized users
def login_is_required(function):
    def wrapper(*args, **kwargs):
        # this method should not be used in production
        if "google_id" not in session:
            return redirect("/")
            # return abort(401)
        else:
            return function()

    return wrapper


@server.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@server.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    try:
        if not session["state"] == request.args["state"]:
            abort(500)  # when state does not match
    except KeyError:
        return redirect("/")

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session["picture"] = id_info.get("picture")

    return redirect("/home")


def get_response(dial, dialogs_json):
    tag = dial[0]['dialog']
    list_of_intents = dialogs_json['dialogs']
    global acc
    if acc > 0.9:
        for i in list_of_intents:
            if i['tag'] == tag:
                result = random.choice(i['responses'])
                break
    else:
        handle_message_alert_event(session["email"])
        result = str("Thank you for your question, I contacted the Admissions Office that will answer your query. "
                     "Please wait a moment.")

    return result


def bot_response(msg):
    dials = predict_class(msg, model)
    response = get_response(dials, dialogs)
    return response


@server.route("/logout")
def logout():
    session.pop("google_id")
    return redirect("/")


@server.route("/")
def index():
    return render_template("index.html")


@server.route("/home")
@login_is_required
def home():
    user_email = session['email']
    user_name = session['name']

    messages = ChatLog.query.filter(ChatLog.msg_session.endswith(user_email)).all()
    roles = ChatLog.query.filter(ChatLog.user_role.endswith("client")).all()

    logged_user_exists = LoggedInUsers.query.filter_by(log_user_email=user_email).first()
    if not logged_user_exists:
        user_info = LoggedInUsers(log_user_name=user_name, log_user_email=user_email)
        db.session.add(user_info)
        db.session.commit()

    return render_template("home.html", room_id=user_email, roles=roles, messages=messages)


@server.route("/get")
def get_bot_response():
    ''' GET MESSAGE FROM CLIENT/FRONTEND THEN GIVE BOT RESPONSE '''
    user_message = request.args.get('msg')
    user_email = session['email']
    date = datetime.datetime.now()
    current_time = date.strftime("%c")

    bot_name = 'Maki Bot'
    bot_reply = bot_response(user_message)
    bot_role = "chat bot"

    ''' RECORD THE MESSAGE AND WHO IT CAME FROM IN THE CHAT USERS AND CHAT LOGS DATABASE '''
    bot_message = ChatLog(message=bot_reply, timestamp=current_time, msg_from=bot_name, msg_session=user_email,
                          user_role=bot_role)
    db.session.add(bot_message)
    db.session.commit()
    return bot_reply


@server.route("/get_client_message")
def get_client_message():
    user_message = request.args.get('message')
    user_email = session['email']
    user_name = session['name']
    user_role = "client"
    date = datetime.datetime.now()
    current_time = date.strftime("%c")

    user_chat = ChatLog(message=user_message, timestamp=current_time, msg_from=user_name, msg_session=user_email,
                        user_role=user_role)
    db.session.add(user_chat)
    db.session.commit()

    return 'Applicant message received.'


@socket_.on('send_message')
def handle_send_message_event(data):
    socket_.emit('receive_message', data, room=data['channel'])


@socket_.on('message_received')
def handle_message_alert_event(data):
    if acc < 0.8:
        chat_user = ChatLog.query.filter_by(msg_session=session['email']).first()
        chat_datastore.toggle_active(chat_user)
        print("Probability is below 80%.")
        print("Message alert received in main.")
        socket_.emit('message_alert', data, broadcast=True)
        email_to_notify = Contacts.query.all()
        print(f'Current user is: {session["email"]}')

        offline_contacts = []
        for user in email_to_notify:
            if user.is_active:
                offline_contacts.append(user.email)

        print(f"Contacts that are offline: {offline_contacts}")

        with mail.connect() as conn:
            for users in offline_contacts:
                message = f"Applicant's Name: {session['name']}\n" \
                          "This is a notification to inform you that an applicant has a query that Maki Bot cannot " \
                          "answer yet.\nGo to the admission website http://127.0.0.1:5000/admin/home-admin to see and " \
                          "answer the query. "
                subject = "This is a notification to answer an applicant's query"
                msg = Message(recipients=[users],
                              body=message,
                              subject=subject,
                              sender=server.config.get("MAIL_USERNAME"))
                conn.send(msg)
                print(f"sent to: {users}")
    return "sent"


@socket_.on('join')
def on_join(data):
    room = data['channel']
    join_room(room)
    emit("Room: " + str(room), room=room)
    print(f"joined the room: {room}")


contact_security = Security(server, contact_datastore, login_form=server.route("/login"))