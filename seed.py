from app import app
from models import db, User, Feedback

db.drop_all()
db.create_all()

user = User.register(
    username = "tony",
    password = "secret",
    email = "tony@test.com",
    first_name = "tony1",
    last_name = "touch"
)

user = User.register(
    username = "nessa",
    password = "secret",
    email = "nessa@test.com",
    first_name = "nessa",
    last_name = "touch"
)

fb1 = Feedback(
    title = "testtitle1",
    content = "testcontent1",
    username = "tony"
)

fb2 = Feedback(
    title = "testtitle2",
    content = "testcontent2",
    username = "tony"
)

db.session.commit()