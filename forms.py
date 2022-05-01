from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, IntegerField, PasswordField, SelectField, BooleanField
from wtforms.validators import InputRequired, NumberRange, Optional, Email, Length

class AddUserForm(FlaskForm):
    
    # username - a unique primary key that is no longer than 20 characters.
    username = StringField("Username", validators=[InputRequired(), Length(max=20)])
    # password - a not-nullable column that is text
    password = PasswordField("Password", validators=[InputRequired()])
    # email - a not-nullable column that is unique and no longer than 50 characters.
    email = EmailField("Email", validators=[Email(message="Please enter a valid email address."), Length(max=50)])
    # first_name - a not-nullable column that is no longer than 30 characters.
    first_name = StringField("First Name", validators=[InputRequired(), Length(max=30)])
    # last_name - a not-nullable column that is no longer than 30 characters.
    last_name = StringField("Last Name", validators=[InputRequired(), Length(max=30)])
    
class LoginUserForm(FlaskForm):
    
    # username - a unique primary key that is no longer than 20 characters.
    username = StringField("Username", validators=[InputRequired(), Length(max=20)])
    # password - a not-nullable column that is text
    password = PasswordField("Password", validators=[InputRequired()])
    
    
class AddFeedbackForm(FlaskForm):
    
    # title - a not-nullable column that is at most 100 characters
    title = StringField("Title", validators=[InputRequired(), Length(max=100)])
    # content - a not-nullable column that is text
    content = StringField("Content", validators=[InputRequired()])

class EditFeedbackForm(FlaskForm):
    
    # title - a not-nullable column that is at most 100 characters
    title = StringField("Title", validators=[InputRequired(), Length(max=100)])
    # content - a not-nullable column that is text
    content = StringField("Content", validators=[InputRequired()])