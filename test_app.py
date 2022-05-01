from unittest import TestCase

from app import app
from models import db, User, Feedback

# Use test database and don't clutter tests with SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///hashing_db_test'
app.config['SQLALCHEMY_ECHO'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):
    """Tests for views for User."""
    
    def setUp(self):
        """Add sample user."""

        Feedback.query.delete()
        User.query.delete()
        db.session.commit()

        user = User.register(
            username = "test_u1",
            password = "test_secret",
            email = "test_u1@test.com",
            first_name = "test_f",
            last_name = "test_l"
        )
        db.session.add(user)
        db.session.commit()

        self.username = user.username
        self.password = user.password

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()
        
    def test_404(self):
        """Test that invalid urls go to custom 404 page."""
        with app.test_client() as client:
            resp = client.get('/asvohh', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("Oops", html)
        
    def test_302_redirect_for_non_logged_in_users(self):
        """Test that non-logged-in users are taken to register page."""
        
        with app.test_client() as client:
            resp = client.get('/')

            self.assertEqual(resp.status_code, 302)

    def test_show_register_on_redirect_for_non_logged_in_users(self):
        """Test that users are shown register page."""
        
        with app.test_client() as client:
            resp = client.get('/', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Register", html)
            self.assertIn("Username", html)
            self.assertIn("Password", html)
        
    def test_register_get_request(self):
        """Test register GET requests."""

        with app.test_client() as client:
            resp = client.get('/register')
            html = resp.get_data(as_text=True)
        
            self.assertIn("Register", html)
            self.assertIn("Username", html)
            self.assertIn("Password", html)
        
    def test_register_post_request(self):
        """Test that register POST requests redirect."""

        with app.test_client() as client:
            resp = client.post(
                "/register", json={
                    "username" : "test_u3",
                    "password" : "test_secret",
                    "email" : "test_u3@test.com",
                    "first_name" : "test_f3",
                    "last_name" : "test_l3",
                }),
            
            # follow redirect to user's page
            self.assertEqual(resp[0].status_code, 302)
            self.assertEqual(User.query.count(), 2)
            
    def test_register_post_request_followed(self):
        """Test register POST requests."""

        with app.test_client() as client:
            resp = client.post(
                "/register", json={
                    "username" : "test_u3",
                    "password" : "test_secret",
                    "email" : "test_u3@test.com",
                    "first_name" : "test_f3",
                    "last_name" : "test_l3",
                }, follow_redirects=True),
            
            html = resp[0].get_data(as_text=True)
            
            self.assertIn("test_u3", html)
            self.assertEqual(resp[0].status_code, 200)
            self.assertEqual(User.query.count(), 2)      
            
    def test_login_get_request(self):
        """Test login GET requests."""
        
        with app.test_client() as client:
            resp = client.get('/login')
            html = resp.get_data(as_text=True)
            
            self.assertIn("Username", html)
            self.assertIn("Password", html)
            self.assertNotIn("Email", html)
            self.assertNotIn("First Name", html)
            
    def test_login_post_request(self):
        """Test that login POST requests redirect."""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['user_id'] = self.username

            resp = client.post(
                "/login", data={
                    "username" : self.username,
                    "password" : "test_secret"
                }),

            # follow redirect to user's page
            self.assertNotIn("Bad name/password", resp[0].text)
            self.assertEqual(resp[0].status_code, 302)
            
    def test_login_post_request_followed(self):
        """Test login POST requests."""

        with app.test_client() as client:
            resp = client.post(
                "/login", data={
                    "username" : self.username,
                    "password" : "test_secret",
                }, follow_redirects=True),
            
            html = resp[0].get_data(as_text=True)
            
            self.assertNotIn("Bad name/password", resp[0].text)
            self.assertEqual(resp[0].status_code, 200)
            self.assertIn(self.username, html)
            
    def test_user_page_non_logged_in_session_redirect(self):
        """Test if a non-logged in user attempts to view another user's page, then redirects to /."""
        
        with app.test_client() as client:

            resp = client.get(f'/users/{self.username}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertIn("<a href=\"/\">", html)
            
    def test_user_page_wrong_user_redirect(self):
        """Test if a different user attempts to another user's page, then redirects to their own page."""
        
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['user_id'] = "test_invalid_user"

            resp = client.get(f'/users/{self.username}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertIn("test_invalid_user", html)
            
    def test_user_page_followed(self):
        """Test that user page appears for logged-in user."""
        
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['user_id'] = self.username

            resp = client.get(f'/users/{self.username}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.username, html)
            self.assertIn("Details", html)

    def test_that_user_a_cannot_delete_user_b(self):
        """Test that User A cannot delete User B by visiting the users/[username]/delete URL."""
        with app.test_client() as client:
            
            user_a = "test_invalid_user"
            user_b = self.username
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a
            
            resp = client.get(f'/users/{user_b}/delete')
            html = resp.get_data(as_text=True)
            
            self.assertIn(f"/users/{user_a}", html)
            self.assertEqual(resp.status_code, 302)

    def test_that_user_a_cannot_delete_user_b_followed(self):
        """Test that User A cannot delete User B by visiting the users/[username]/delete URL."""
        with app.test_client() as client:
            
            user_a = "test_invalid_user"
            user_b = self.username
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a
            
            resp = client.get(f'/users/{user_b}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Cannot delete other users", html)
    
    def test_user_deletion_followed(self):
        """Test that a user is deleted properly."""
        with app.test_client() as client:
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = self.username
            
            resp = client.post(f'/users/{self.username}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("Register", html)
            self.assertIn("Username", html)
            self.assertIn("Password", html)


class FeedbackViewsTestCase(TestCase):
    """Tests for Feedback for User."""
    
    def setUp(self):
        """Add sample user."""

        Feedback.query.delete()
        User.query.delete()
        db.session.commit()

        user_a = User.register(
            username = "test_u1",
            password = "test_secret",
            email = "test_u1@test.com",
            first_name = "test_f1",
            last_name = "test_l1"
        )
        user_b = User.register(
            username = "test_u2",
            password = "test_secret",
            email = "test_u2@test.com",
            first_name = "test_f2",
            last_name = "test_l2"
        )
        feedback_a = Feedback(
            title = "test_title_a",
            content = "test_content_a",
            username = "test_u1"
        )
        feedback_b = Feedback(
            title = "test_title_b",
            content = "test_content_b",
            username = "test_u2"
        )
        db.session.add(user_a)
        db.session.add(user_b)
        db.session.add(feedback_a)
        db.session.add(feedback_b)
        db.session.commit()

        self.username_a = user_a.username
        self.username_b = user_b.username
        self.password_a = user_a.password
        self.password_b = user_b.password
        
        self.feedback_a = feedback_a
        self.feedback_b = feedback_b
        
        self.title_a = feedback_a.title
        self.content_a = feedback_a.content
        self.title_b = feedback_b.title
        self.content_b = feedback_b.content

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()
        
    def test_feedback_add_get_request_for_invalid_user_redirect(self):
        """Test that User A cannot see the feedback page for User B, and instead goes to their own feedback page."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            user_b = self.username_b
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/users/{user_b}/feedback/add')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 302)
            self.assertIn(f"{user_a}", html)
        
    def test_feedback_add_get_request_for_invalid_user_followed(self):
        """Test that User A cannot see the feedback page for User B, and instead redirects to their own feedback page."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            user_b = self.username_b
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/users/{user_b}/feedback/add', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"for {user_a}", html)
        
    def test_feedback_add_get_request_for_valid_user(self):
        """Test that the Feedback form page appears."""
        
        with app.test_client() as client:
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = self.username_a

            resp = client.get(f'/users/{self.username_a}/feedback/add', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn("Title", html)
            self.assertIn("Content", html)
            self.assertEqual(resp.status_code, 200)
        
    def test_feedback_add_post_request(self):
        """Test that the Feedback form submission redirects to user details page."""
        
        with app.test_client() as client:
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = self.username_a

            resp = client.post(f'/users/{self.username_a}/feedback/add',
                json={
                    "title":"adding_feedback",
                    "content":"new content"
                }, follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn(self.username_a, html)
            self.assertIn("adding_feedback", html)
            self.assertIn("new content", html)
            self.assertEqual(resp.status_code, 200)

    def test_feedback_id_update_get_request_for_non_logged_in_user_redirect(self):
        """Test that non-logged-in user always redirects to home."""
        
        with app.test_client() as client:

            resp = client.get('/feedback/11/update')
            self.assertEqual(resp.status_code, 302)

            resp = client.get('/feedback/14352351/update')
            self.assertEqual(resp.status_code, 302)

    def test_feedback_id_update_get_request_for_non_logged_in_user_followed(self):
        """Test that non-logged-in user always redirects to home."""
        
        with app.test_client() as client:

            resp = client.get('/feedback/11/update', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Register", html)
            self.assertIn("Username", html)
            self.assertIn("Password", html)

            resp = client.get('/feedback/14352351/update', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Register", html)
            self.assertIn("Username", html)
            self.assertIn("Password", html)

    def test_invalid_feedback_id_update_get_request_redirect(self):
        """Test that an invalid feedback id is redirected to home."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get('/feedback/972322/update')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 302)

    def test_invalid_feedback_id_update_get_request_followed(self):
        """Test that an invalid feedback id is redirected to home."""
        
        with app.test_client() as client:
            
            resp = client.get('/feedback/972322/update', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Register", html)
            self.assertIn("Username", html)
            self.assertIn("Password", html)

    def test_valid_feedback_id_update_get_request_for_invalid_user_redirect(self):
        """Test that User A cannot update feedback for User B, and instead goes to their own feedback page."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/feedback/{self.feedback_b.id}/update')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 302)
            self.assertIn(f"{user_a}", html)

    def test_valid_feedback_id_update_get_request_for_invalid_user_followed(self):
        """Test that User A cannot update feedback for User B, and instead goes to their own feedback page."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/feedback/{self.feedback_b.id}/update', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"{user_a}", html)

    def test_valid_feedback_id_update_post_request_for_valid_user_redirect(self):
        """Test that User A successfully updates feedback."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.post(f'/feedback/{self.feedback_a.id}/update',
                json={
                    "title":"new title",
                    "content":"new content"
                }
            )
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 302)
            self.assertIn(f"{user_a}", html)

    def test_valid_feedback_id_update_post_request_for_valid_user_redirect(self):
        """Test that User A successfully updates feedback."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.post(f'/feedback/{self.feedback_a.id}/update',
                json={
                    "title":"new title",
                    "content":"new content"
                }, follow_redirects=True
            )
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("changes saved!", html)
            self.assertIn(f"{user_a}", html)
        
    def test_that_user_a_cannot_delete_feedback_b_redirect(self):
        """Test that User A cannot delete User B's feedback."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/feedback/{self.feedback_b.id}/delete')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 302)
        
    def test_that_user_a_cannot_delete_feedback_b_followed(self):
        """Test that User A cannot delete User B's feedback."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/feedback/{self.feedback_b.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(user_a, html)
        
    def test_that_user_a_deletes_feedback_a(self):
        """Test that User A cannot delete User B's feedback."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            feedback_a = self.feedback_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get(f'/feedback/{feedback_a.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(feedback_a.title, html)
    
    def test_logout_redirect(self):
        """Test that a user successfully logs out."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get('/logout')
            
            self.assertEqual(resp.status_code, 302)
    
    def test_logout_followed(self):
        """Test that a user successfully logs out and is redirected to /."""
        
        with app.test_client() as client:
            
            user_a = self.username_a
            
            with client.session_transaction() as change_session:
                change_session['user_id'] = user_a

            resp = client.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            # ensure the 'logout' button is not in html to confirm that we've been logged out
            self.assertNotIn("logout", html)
            # ensure there are no appearances of username in rendered HTML
            self.assertNotIn(user_a, html)