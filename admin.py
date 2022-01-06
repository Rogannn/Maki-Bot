import json
import subprocess
import time

import regex

from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO, join_room, emit, leave_room
from sqlalchemy.exc import IntegrityError
import datetime
from flask_security import Security
from flask_security.utils import hash_password, verify_password
from main import db, ChatLog, LoggedInUsers, Contacts, AdminLogin, NewQuestion, contact_datastore, admin_datastore, \
    chat_datastore, faqs_datastore

app = Flask(__name__)
app.debug = True
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'ntcmm7xqp2ujkjr'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = 'ryootb97lfwkie9'
socket_ = SocketIO(app, cors_allowed_origins='*', manage_session=True)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_BINDS'] = {
    'all_chats': 'sqlite:///db/chat_log.sqlite3',
    'to_login': 'sqlite:///db/admin_account.sqlite3',
    'to_notify': 'sqlite:///db/contacts.sqlite3',
    'logged_in': 'sqlite:///db/logged_users.sqlite3',
    'faqs': 'sqlite:///db/new_question.sqlite3'
}

db.init_app(app)
db.create_all(bind=['all_chats', 'to_login', 'to_notify', 'logged_in', 'faqs'])

sec = Security()

contact_security = Security(app, name=contact_datastore, login_form=app.route("/"))
admin_security = Security(app, name=admin_datastore, login_form=app.route("/"))
sec.init_app(app, contact_security, admin_security)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first!")
            return redirect(url_for('login_page'))

    return wrap


@app.route('/callback')
def callback():
    return redirect('/admin/home-admin')


@app.route("/", methods=["GET", "POST"])
def login_page():
    ''' INDEX + LOGIN PAGE '''
    if request.method == "POST":
        # GET USERNAME AND PASSWORD FROM HTML
        uname = request.form["uname"]
        passw = request.form.get("passw")

        # CHECK DB IF USERNAME AND PASSWORD EXISTS
        admin_user = AdminLogin.query.filter_by(username=uname).first()
        contact_user = Contacts.query.filter_by(username=uname).first()

        # LOGIN IF USERNAME AND PASSWORD IS CORRECT
        try:
            admin_dict = dict((col, getattr(admin_user, col)) for col in admin_user.__table__.columns.keys())
            admin_hashed_pass = admin_dict.get('password')
            admin_password_verified = verify_password(passw, admin_hashed_pass)
            if admin_password_verified:
                session["logged_in"] = True
                session["username"] = admin_dict.get('username')
                session["user_role"] = "Admin"
                return redirect(url_for("callback"))
        except AttributeError:
            try:
                contact_dict = dict((col, getattr(contact_user, col)) for col in contact_user.__table__.columns.keys())
                contact_hashed_pass = contact_dict.get('password')
                contact_password_verified = verify_password(passw, contact_hashed_pass)
                if contact_password_verified:
                    session["logged_in"] = True
                    session["username"] = contact_dict.get('username')
                    session["user_role"] = "Contact"
                    return redirect(url_for("callback"))
            except AttributeError:
                flash("Username or Password is incorrect.")
                return redirect(url_for("login_page"))
            return redirect(url_for("login_page"))
    return render_template("login-admin.html")


@app.route("/home-admin", methods=["GET", "POST"])
@login_required
def home():
    ''' QUERY ALL DATABASES '''
    print(session["username"])
    admin = AdminLogin.query.all()
    contacts = Contacts.query.all()
    logged_user = LoggedInUsers.query.all()
    test = ChatLog.query.all()

    admin_user = AdminLogin.query.filter_by(username=session['username']).first()
    contact_user = Contacts.query.filter_by(username=session['username']).first()

    if session["user_role"] == "Admin":
        for a in admin:
            if a.active and a.username == session['username']:
                admin_datastore.toggle_active(admin_user)
                db.session.commit()
    else:
        for c in contacts:
            if c.active and c.username == session['username']:
                contact_datastore.toggle_active(contact_user)
                db.session.commit()

    online_admins_indicator(session["username"])

    ''' FOR ALERTING NEW QUERY '''
    msg_email = [msg.msg_session for msg in ChatLog.query.all()]
    msg_answered = [msg.active for msg in ChatLog.query.all()]

    ''' COMPUTING TOTAL NUMBERS OF ALL ACCOUNTS '''
    admin_count = []
    contact_count = []
    applicant_count = []
    for user in admin:
        admin_count.append(user.id)
    for user in contacts:
        contact_count.append(user.id)
    for user in logged_user:
        applicant_count.append(user.id)

    return render_template("home-admin.html", logged_user=logged_user, admin=admin, test=test,
                           applicant_count=len(applicant_count), msg_email=msg_email, msg_answered=msg_answered,
                           contacts=contacts, contact_count=len(contact_count), admin_count=len(admin_count))


@app.route("/show_message/<email>", methods=["GET", "POST"])
@login_required
def show_message(email):
    messages = ChatLog.query.filter(ChatLog.msg_session.endswith(email)).all()
    roles = ChatLog.query.with_entities(ChatLog.user_role)
    client = LoggedInUsers.query.filter(LoggedInUsers.log_user_email.endswith(email)).all()

    chat_user = ChatLog.query.filter_by(msg_session=email).first()
    if chat_user.active == 1:
        chat_datastore.toggle_active(chat_user)

    # count messages of an applicant with maki bot
    list_of_msg = []
    for msg in messages:
        list_of_msg.append(msg.id)
    print(len(list_of_msg))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        template_name = 'chatlog.html'
    else:
        template_name = 'home-admin.html'
    return render_template(template_name, messages=messages, room_id=email, roles=roles, client=client)


@app.route("/contact-account", methods=["GET", "POST"])
@login_required
def contact_account():
    ''' ADD CONTACT ACCOUNT '''
    if request.method == "POST":
        contact_datastore.create_user(
            firstname=request.form.get('fname'),
            middle=request.form.get('mname'),
            lastname=request.form.get('lname'),
            email=request.form.get('mail'),
            username=request.form.get('uname'),
            password=hash_password(request.form.get('pass'))
        )
        try:
            # contact_datastore.add_role_to_user(request.form.get('uname'), "contact")
            db.session.commit()
            flash("Successfully added.")
        except IntegrityError:
            db.session.rollback()
            flash("Username or E-mail already exists.")

        return redirect(url_for("contact_account"))

    contacts = Contacts.query.all()
    return render_template("contact-account.html", contacts=contacts)


@app.route("/admin-account", methods=["GET", "POST"])
@login_required
def admin_account():
    ''' ADD ADMIN ACCOUNT '''
    if request.method == "POST":
        admin_datastore.create_user(
            firstname=request.form.get('fname'),
            middle=request.form.get('mname'),
            lastname=request.form.get('lname'),
            email=request.form.get('mail'),
            username=request.form.get('uname'),
            password=hash_password(request.form.get('pass'))
        )
        try:
            # admin_datastore.add_role_to_user(request.form.get('uname'), "admin")
            db.session.commit()
            flash("Successfully added.")
        except IntegrityError:
            db.session.rollback()
            flash("Username or E-mail already exists.")

        return redirect(url_for("admin_account"))

    ''' SHOW ACCOUNTS '''
    admin = AdminLogin.query.all()
    return render_template("admin-account.html", admins=admin)


@app.route("/admin-logout")
@login_required
def logout():
    name = session["username"]
    admin_user = AdminLogin.query.filter_by(username=name).first()
    contact_user = Contacts.query.filter_by(username=name).first()
    if session["user_role"] == "Admin":
        admin_datastore.toggle_active(admin_user)
        db.session.commit()
    if session["user_role"] == "Contact":
        contact_datastore.toggle_active(contact_user)
        db.session.commit()

    session.pop("logged_in")
    session.pop("user_role")
    session.pop("username")
    flash("You have been logged out.")
    return redirect(url_for("login_page"))


@app.route('/get_training_data', methods=["GET", "POST"])
def get_training_data():
    msg = request.args.getlist('msg[]')
    to_tag = msg[0]
    new_tag = regex.sub('[^A-Za-z0-9]+', '', to_tag)
    print(f"query: {msg[0]}\nresponse: {msg[1]}")
    new_msg = {"tag": f"{new_tag}",
               "triggers": [f"{msg[0]}"],
               "responses": [f"{msg[1]}"]
               }
    # ADD TO DATABASE
    date = datetime.datetime.now()
    current_time = date.strftime("%c")
    new_faq = NewQuestion(question=msg[0], answer=msg[1], question_created=current_time)
    db.session.add(new_faq)
    db.session.commit()

    # learn_this(new_msg)

    return redirect(url_for('home'))


def learn_this(new_data, filename='dialogs.json'):
    with open(filename, 'r+') as file:
        file_data = json.load(file)
        file_data["dialogs"].append(new_data)
        file.seek(0)
        json.dump(file_data, file, indent=4)
    print("Starting training...")
    subprocess.call("training.py", shell=True)


@app.route("/delete_contact/<contact_id>", methods=["GET", "POST"])
@login_required
def delete_contact(contact_id):
    Contacts.query.filter(Contacts.id == contact_id).delete()
    db.session.commit()
    flash("Deleted successfully.")
    return redirect(url_for('contact_account'))


@app.route("/delete_admin/<admin_id>", methods=["GET", "POST"])
@login_required
def delete_admin(admin_id):
    ''' DELETE ADMIN ID '''
    AdminLogin.query.filter(AdminLogin.id == admin_id).delete()
    db.session.commit()
    flash("Deleted successfully.")
    return redirect(url_for('admin_account'))


@app.route("/admin_msg", methods=["GET", "POST"])
def get_admin_message():
    user_email = request.args.get('email')

    admin_message = request.args.get('message')
    admin_name = "ADMISSION ADMIN"
    admin_role = "admin"
    current_time = datetime.datetime.now()

    admin_chat = ChatLog(timestamp=current_time, message=admin_message, msg_from=admin_name,
                         msg_session=user_email, user_role=admin_role)
    db.session.add(admin_chat)
    db.session.commit()

    return admin_message


# admins = contact and admin, admin = admin only
@socket_.on('online_admins')
def online_admins_indicator(data):
    print("online_admins_indicator is called.")
    socket_.emit('on_admins_indicator', data, broadcast=True)


@socket_.on('offline_admins')
def offline_admins_indicator(data):
    socket_.emit('off_admins_indicator', data, broadcast=True)


@socket_.on('join')
def on_join(data):
    room = data['channel']
    join_room(room)
    emit("Room: " + str(room), room=room)
    print(f"Admin has joined the room: {room}")


@socket_.on('leave')
def on_leave(data):
    room = data['channel']
    leave_room(room)
    emit("Room: " + str(room), room=room)
    print(f"Admin has left the room: {room}")


@socket_.on('disconnect')
def disconnect_user():
    print("admin has disconnected")
    admin_user = AdminLogin.query.filter_by(username=session['username']).first()
    admin_db = AdminLogin.query.all()
    for a in admin_db:
        if not a.active and a.username == session['username']:
            admin_datastore.toggle_active(admin_user)

    session.pop("logged_in")
    session.pop("user_role")
    session.pop("username")


@socket_.on('send_message')
def handle_send_message_event(data):
    socket_.emit('receive_message', data, room=data['room'])


@socket_.on('message_received')
def handle_message_alert_event(data):
    print("Message alert received in admin")
    socket_.emit('message_alert', data, broadcast=True)
