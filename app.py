from flask import Flask, render_template, flash, redirect, render_template, session, request
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback

from forms import AddUserForm, LoginUserForm, AddFeedbackForm, EditFeedbackForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "oh-so-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hashing_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

debug = DebugToolbarExtension(app)

connect_db(app)

# app name
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")

@app.route("/")
def show_index():
    """Redirect to /register."""
    
    if session.get("user_id"):
        user = User.query.get_or_404(session["user_id"])
        
        # if user is logged in, redirect to user page
        return redirect(f'/users/{user}')
    
    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def handle_register():
    """Handle GET and POST requests to /register."""
    
    form = AddUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.username
        return redirect(f"/users/{user.username}")
    
    else:
        return render_template("register.html", form=form)
    
@app.route("/login", methods=["GET", "POST"])
def handle_login():
    """Handle GET and POST requests to /login."""
    
    form = LoginUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username=username, password=password)

        if user:
            session["user_id"] = user.username
            return redirect(f"/users/{username}")
        
        else:
            flash("Wrong username or password.", "error")
            form.username.errors = ["Bad name/password"]
        
    return render_template("login.html", form=form)

    
@app.route("/users/<username>")
def show_user_details(username):
    """Return the text “You made it!”"""
    
    # Show user details if session id matches user url
    if session.get("user_id") == username:
        user = User.query.get(username)
        return render_template("user.html", user=user)
    
    # else redirect them to their own user details if they are a different user
    elif session.get("user_id"):
        user = session["user_id"]
        return redirect(f"/users/{user}")
    
    # else redirect to home if they are not logged in
    else:
        return redirect("/")

@app.route("/users/<username>/delete", methods=["GET", "POST"])
def delete_user(username):
    """
    Remove user, remove all feedback, and clear user info from session.
    Redirect to /.
    """
    
    if request.method == 'POST' and session.get("user_id") == username:
            
        # find the user
        user = User.query.get_or_404(username)

        # delete from db
        db.session.delete(user)
        db.session.commit()
        
        # clear session
        session.pop("user_id")

        # return to redirect
        return redirect("/")

    else:
        flash("Cannot delete other users.", "error")
        return redirect(f"/users/{session['user_id']}")
    
    
# ----------------------------------------------------------------
# Feedback views
# ----------------------------------------------------------------
@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def handle_feedback_add(username):
    """
    Handle GET and POST requests for adding feedback.
    Display a form to add feedback Make sure that only the user who is logged in can see this form
    """
    
    # Show feedback form if session id matches user url
    if session.get("user_id") == username:
            
        form = AddFeedbackForm()
        
        # find the user
        user = User.query.get_or_404(username)
        
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            
            # create instance of Feedback object
            feedback = Feedback(title=title, content=content, username=username)
            
            # add feedback to database
            db.session.add(feedback)
            db.session.commit()
            
            # return user back to username page
            return redirect(f"/users/{username}")
        
        else:
            return render_template("/feedback/add.html", form=form, user=user)

    # else redirect them to their own user feedback form if they are a different user
    elif session.get("user_id"):
        user = session["user_id"]
        return redirect(f"/users/{user}/feedback/add")
    
    # else redirect to home if they are not logged in
    return redirect("/")
            
@app.route("/feedback/<int:id>/update", methods=["GET", "POST"])
def handle_feedback_update(id):
    """
    Handle GET and POST requests for adding feedback.
    Display a form to edit feedback — 
    Update a specific piece of feedback and redirect to /users/
    **Make sure that only the user who has written that feedback can see this form.
    """
    if session.get('user_id') is None:
        return redirect('/')
    
    # request feedback item
    try:
        feedback = Feedback.query.filter_by(id=id).one()
    except:
        # if feedback item does not exist
        flash(f"Feedback item {id} does not exist", "error")
        return redirect('/')
    
    # request the user who wrote the feedback
    user = User.query.get_or_404(feedback.username)
            
    # if the current user matches the feedback item's username
    if session.get("user_id") == feedback.username:
        form = EditFeedbackForm(obj=feedback)
    
        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data
            
            # update feedback to database
            db.session.commit()
            
            # return user back to username page
            flash("changes saved!", "success")
            return redirect(f"/users/{user}")
        
        else:
            return render_template("/feedback/edit.html", form=form, user=user, feedback=feedback)
        
    # else if current user does not match feedback item's username, redirect to user's page
    elif session.get("user_id"):
        flash(f"Feedback item {id} belongs to another user. Please select a feedback item from the list below.", "error")
        return redirect(f"/users/{session['user_id']}")
    
    # else if not logged in, return to home
    return redirect("/")

@app.route("/feedback/<int:id>/delete", methods=["GET", "POST"])
def delete_feedback(id):
    """
    Delete a specific piece of feedback and redirect to /users/ — 
    Make sure that only the user who has written that feedback can delete it
    """
    
    # request feedback item
    try:
        feedback = Feedback.query.filter_by(id=id).one()
    except:
        # if feedback item does not exist
        flash(f"Feedback item {id} does not exist", "error")
        return redirect('/')
    
    # request the user who wrote the feedback
    user = User.query.get_or_404(feedback.username)
    
    if session.get("user_id") == feedback.username:
        
        db.session.delete(feedback)
        db.session.commit()
        
        flash(f'Feedback item {id} deleted.', "success")
        return redirect(f'/users/{user}')
    
    elif session.get("user_id"):
        flash(f'Feedback item {id} belongs to another user. Please select a feedback item below.', "error")
        return redirect(f'/users/{user.username}')

    else:
        return redirect('/')
    
@app.route("/logout")
def handle_logout():
    """Log the user and remove them from the session."""
    
    if session.get("user_id"):
        session.pop("user_id")
    
    return redirect("/")