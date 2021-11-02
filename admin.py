from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, emit, leave_room
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import func
import datetime
from flask_security import Security
from flask_security.utils import hash_password, verify_password
from main import db, ChatLog, LoggedInUsers, Contacts, AdminLogin, contact_datastore, admin_datastore, chat_datastore

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
app.config['SQLALCHEMY_BINDS'] = {
    'all_chats': 'sqlite:///db/chat_log.sqlite3',
    'to_login': 'sqlite:///db/admin_account.sqlite3',
    'to_notify': 'sqlite:///db/contacts.sqlite3',
    'logged_in': 'sqlite:///db/logged_users.sqlite3'
}

db.init_app(app)
db.create_all(bind=['all_chats', 'to_login', 'to_notify', 'logged_in'])

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
                admin_datastore.toggle_active(admin_user)
                return redirect(url_for("home"))
        except AttributeError:
            try:
                contact_dict = dict((col, getattr(contact_user, col)) for col in contact_user.__table__.columns.keys())
                contact_hashed_pass = contact_dict.get('password')
                contact_password_verified = verify_password(passw, contact_hashed_pass)
                if contact_password_verified:
                    session["logged_in"] = True
                    session["username"] = contact_dict.get('username')
                    session["user_role"] = "Contact"
                    contact_datastore.toggle_active(contact_user)
                    return redirect(url_for("home"))
            except AttributeError:
                flash("Username or Password is incorrect.")
                return redirect(url_for("login_page"))
            return redirect(url_for("login_page"))
    return render_template("login-admin.html")


@app.route("/home-admin", methods=["GET", "POST"])
@login_required
def home():
    ''' SHOW ACCOUNTS '''
    admin = AdminLogin.query.all()
    logged_user = LoggedInUsers.query.all()
    msg_email = [msg.msg_session for msg in ChatLog.query.all()]
    msg_answered = [msg.active for msg in ChatLog.query.all()]
    test = ChatLog.query.all()

    max_logins = db.session.query(func.max(LoggedInUsers.id)).scalar()
    num_of_users = db.session.query(LoggedInUsers).filter(LoggedInUsers.id == max_logins).all()

    return render_template("home-admin.html", logged_user=logged_user, admin=admin, test=test,
                           num_of_users=num_of_users, msg_email=msg_email, msg_answered=msg_answered)


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


@app.route("/update_contact/<contact_id>", methods=["GET", "POST"])
@login_required
def update_contact(contact_id):
    flash("Edit using the textbox below")
    ''' EDIT NAME AND EMAIL '''
    info = Contacts.query.filter_by(id=contact_id).first()
    if info:
        db.session.delete(info)
        db.session.commit()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        db.session.add(name=name)
        db.session.add(email=email)

        db.session.commit()

    return redirect(url_for('contact_account'))


@app.route("/update_admin/<admin_id>", methods=["GET", "POST"])
@login_required
def update_admin(admin_id):
    flash("Edit using the textbox below")
    ''' EDIT NAME AND EMAIL '''
    info = AdminLogin.query.filter_by(id=admin_id).first()
    if info:
        db.session.delete(info)
        db.session.commit()

    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]

        db.session.add(username=uname)
        db.session.add(password=passw)

        db.session.commit()

    return redirect(url_for('admin_account'))


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


@app.route("/delete_all_chats")
@login_required
def delete_all_chat():
    ''' CLEAR THE CHAT LOGS '''
    try:
        delete_chat = db.session.query(ChatLog).delete()
        db.session.commit()
        return redirect("home-admin")
    except KeyError:
        db.session.rollback()
    return render_template("home-admin.html")


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


@socket_.on('send_message')
def handle_send_message_event(data):
    socket_.emit('receive_message', data, room=data['room'])


@socket_.on('message_received')
def handle_message_alert_event(data):
    print("Message alert received in admin")
    socket_.emit('message_alert', data, broadcast=True)
