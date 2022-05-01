from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Create instance of SQLAlchemy
db = SQLAlchemy()

# Create instance of Bcrypt
bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)
    
    
class User(db.Model):
    """User"""

    __tablename__ = "users"

    # username - a unique primary key that is no longer than 20 characters.
    username = db.Column(db.String(20), unique=True, primary_key=True)
    # password - a not-nullable column that is text
    password = db.Column(db.String, nullable=False)
    # email - a not-nullable column that is unique and no longer than 50 characters.
    email = db.Column(db.String(50), nullable=False)
    # first_name - a not-nullable column that is no longer than 30 characters.
    first_name = db.Column(db.String(30), nullable=False)
    # last_name - a not-nullable column that is no longer than 30 characters.
    last_name = db.Column(db.String(30), nullable=False)
    
    feedback = db.relationship('Feedback', backref='user', cascade="all,delete")
    
    
    @classmethod
    def register(cls, username, password, email, first_name, last_name):
    
        """Register user w/ hashed password & return user."""
        
        hashed = bcrypt.generate_password_hash(password)
        # turn hashed bytestring into string
        hashed_utf8 = hashed.decode('utf8')
        
        user = cls(username=username, password=hashed_utf8, email=email, first_name=first_name, last_name=last_name)
        
        # add user to database
        db.session.add(user)
        
        # return instance of user w/ username and hashed password
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """
        Authenticate a user with username and password.
        If user is valid, return user; else return False.
        """
        
        # Query for the user by username.
        user = User.query.filter_by(username=username).first()
        
        # Check that bcrypt returns true in this conditional
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False
        

class Feedback(db.Model):
    """Feedback."""
    
    __tablename__ = "feedback"
    
    # id - a unique primary key that is an auto incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # title - a not-nullable column that is at most 100 characters
    title = db.Column(db.String(100), nullable=False)
    # content - a not-nullable column that is text
    content = db.Column(db.String, nullable=False)
    # username - a foreign key that references the username column in the users table
    # username = db.relationship('User', backref='feedback')
    username = db.Column(db.String, db.ForeignKey("users.username"), nullable=False)