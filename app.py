import os
import pdb

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, EditUserForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    # Log the user out of session if already logged in 
    do_logout()
    
    # Flash a success message 
    flash("Successfully logged out.")
    
    # Navigate back to login page 
    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
                
    # Get the number of likes by the user 
    total_likes = Likes.query.all()
    user_likes = []
    
    for like in total_likes:
        if like.user_id == session[CURR_USER_KEY]:
            user_likes.append(like)
    
    total_user_likes = len(user_likes)
    
    return render_template('users/show.html', user=user, messages=messages, like_count=total_user_likes)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    # Check that the user is logged in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    # Get user from database 
    user_id = session[CURR_USER_KEY]
    user = User.query.get(user_id)
    
    # Create EditUserForm object 
    form = EditUserForm(obj=user)
    
    # Return correct template with correct form 
    if form.validate_on_submit():
        username = user.username 
        password = form.password.data 
        
        validated_user = User.authenticate(username, password)
        
        if validated_user:
            # Get new values from form 
            newUsername = form.username.data 
            newEmail = form.email.data 
            newImageUrl = form.image_url.data 
            newHeaderImageUrl = form.header_image_url.data 
            
            # Edit the user 
            user.username = newUsername 
            user.email = newEmail 
            user.image_url = newImageUrl 
            user.header_image_url = newHeaderImageUrl
            
            db.session.add(user)
            db.session.commit()
            
            # Flash a success message and navigate back to user profile 
            flash("Successfully updated!")
            return redirect(f'/users/{user.id}')
            
        else: 
            flash("Password Incorrect. Try again!")
            return render_template("/users/edit.html", form=form)
    else:
        return render_template("/users/edit.html", form=form)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        # Get a list of all the users that the current user follows 
        following_list = User.query.get(session[CURR_USER_KEY]).following 
        
        # Get the ids of all the users following 
        following_ids = set()
        for user in following_list:
            following_ids.add(user.id)
        
        # Get all messages from all users, ordered by timestamp 
        messages = (Message
                    .query
                    .order_by(Message.timestamp.desc())
                    .all())
                    
        # Filter out messages not by users that the user follows 
        filtered_messages = []
        for message in messages:
            if message.user_id in following_ids:
                filtered_messages.append(message)
        
        # Get the user's likes 
        users_likes = Likes.query.all()
        
        # Get the message ids from user's likes 
        liked_message_ids = []
        for like in users_likes:
            if like.user_id == session[CURR_USER_KEY]:
                liked_message_ids.append(like.message_id)
        
        # Shorten to only show the latest 100 if there are more than 100 posts 
        if len(filtered_messages) < 100:
            return render_template('home.html', messages=filtered_messages, likes=liked_message_ids)
        else:
            shortened_messages = []
            for i in range(0, 100):
                shortened_messages.append(filtered_messages[i])
                return render_template('home.html', messages=shortened_messages, likes=liked_message_ids)
    else:
        return render_template('home-anon.html')
        
###############################################################################
# Like Routes 

@app.route("/users/add_like/<msgId>", methods=["POST"])
def add_remove_like(msgId):
    """Adds/Removes a like"""
    # First, get the message to determine who wrote it 
    message = Message.query.get(msgId)
    
    # Only allow like if message is NOT written by current user 
    if message.user_id != session[CURR_USER_KEY]:
        
        # Get the ids of all the messages that user has already liked 
        user_likes = User.query.get(session[CURR_USER_KEY]).likes
        user_msg_ids = []
        for like in user_likes:
            user_msg_ids.append(like.id)
        
        # If user has already liked message, unlike it 
        if message.id not in user_msg_ids:
            like = Likes(user_id=session[CURR_USER_KEY], message_id=msgId)
            
            db.session.add(like)
            db.session.commit()
            
        else:
            like = Likes.query.filter_by(user_id=session[CURR_USER_KEY], message_id=message.id).first()
            
            db.session.delete(like)
            db.session.commit()

    return redirect('/')

@app.route('/users/<userId>/likes')
def get_likes_page(userId):
    """Displays the likes page"""
    # Get all liked messages 
    liked_messages = User.query.get(userId).likes 
    
    # Get just the ids of liked messages 
    ids = []
    for like in liked_messages:
        ids.append(like.id)
    
    return render_template("/users/likes.html", messages=liked_messages, likes=ids)


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
