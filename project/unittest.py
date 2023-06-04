import unittest
from project import create_app, db
from project.models import User
from werkzeug.security import check_password_hash


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['WTF_CSRF_ENABLED'] = False  
        self.appctx = self.app.app_context()
        self.appctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.drop_all()
        self.appctx.pop()
        self.app = None
        self.appctx = None
        self.client = None

    def test_app(self):
        assert self.app is not None

    def test_Homepage(self):
         response = self.client.get('/', follow_redirects = True)
         assert response.status_code == 200

    def test_Registerform(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 302)

    def test_unlogged_admin(self):
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Assert that the response is a redirect
        assert response.request.path == '/login'  # Assert that the redirect location contains '/login'


    def test_register_user(self):
        response = self.client.post('/register', data={
            'username': 'alice',
            'password': 'foo',
            'confirm_password': 'foo',
        }, follow_redirects=True)
        assert response.status_code == 200
        print(1)
        print(response)
        assert response.request.path == '/login' # redirected to login


        # login with new user
        response = self.client.post('login', data={
            'username': 'alice',
            'password': 'foo',
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        print(html)
        assert 'alice' in html













    def test_XSS(self):
        response = self.client.post('/register', data={
            'username': '<script> alert("XSS");</script>',
            'password' : 'COMPLEX123'
            'confirm_password': 'COMPLEX123'
        }, follow_redirects=True)
        assert response.status_code == 200

        response = self.client.post('/login', data={
            'username': '<script> alert("XSS");</script>',
            'password': 'COMPLEX123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert '<script> alert("XSS");</script>' not in response.get_data(as_text=True)


    def test_Password_Hashes(self):
        response = self.client.post('/register', data = {
            'username' : 'alice',
            'password' : 'COMPLEX123'
            'confirm_password': 'COMPLEX123'
        }, follow_redirects = True)
        assert response.status_code == 200
        # should redirect to the login page
        assert response.request.path == '/login'

        user = User.query.filter_by(username='alice').first()
        assert user is not None
        assert check_password_hash(user.password, 'COMPLEX123')

    def test_sqli(self):
        response = self.client.post('/register', data = {
            'username' : 'alice"; drop table user; --',
            'password' : 'COMPLEX123'
            'confirm_password': 'COMPLEX123'
        }, follow_redirects = True)
        assert response.status_code == 200 
        user = User.query.filter_by(username='admin').first()
        assert user is not None

    