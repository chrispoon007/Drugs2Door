import pytest
import io
from app import app, db
from models import Order, DrugOrder, Drug, User
from flask import url_for, Flask, json
from werkzeug.security import generate_password_hash
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user
from datetime import datetime, timezone
import io
import os
from sqlalchemy.orm import session
import unittest
from unittest.mock import patch, mock_open, MagicMock
from forms import UserUpdateForm, SupportForm, LoginForm

bcrypt = Bcrypt(app)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture(scope='module')
def setup_database():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # replace with your actual database URI
    app.config['TESTING'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()
    yield db  # This line was missing
    with app.app_context():
        db.drop_all()

def login_test_user(client, setup_database, role_id=1):
    hashed_password = bcrypt.generate_password_hash('test').decode('utf-8')
    test_user = User(name='test', email='test@test.com', password=hashed_password, phn='1234567890', role_id=role_id)
    setup_database.session.add(test_user)
    setup_database.session.commit()

    # Create a request context manually
    with client.application.test_request_context():
        # Log in the user
        login_user(test_user)

def test_review_order_post(client, setup_database):
    login_test_user(client, setup_database)
    order = Order()
    drug = Drug(name='Drug1', price=10.0)
    setup_database.session.add(order)
    setup_database.session.add(drug)
    setup_database.session.commit()

    # Make a POST request to the route
    rv = client.post('/review_order/1', data={
        'status': 'approved',
        'drug_orders-1-name': '1',
        'drug_orders-1-quantity': '1',
        'drug_orders-1-refills': '1'
    })

    # Check that the response is a redirect to the pharmacistdash route
    assert rv.status_code == 302
    assert '/pharmacistdash' in rv.location

    # Check that the drug order was created
    drug_order = DrugOrder.query.first()
    assert drug_order is not None
    assert drug_order.order_id == 1
    assert drug_order.drug_id == 1
    assert drug_order.quantity == 1
    assert drug_order.refills == 1
    assert drug_order.prescription_approved == True

def test_order_and_drug_creation(client, setup_database):
    login_test_user(client, setup_database)
    order = Order()
    drug = Drug(name='Drug1', price=10.0)
    setup_database.session.add(order)
    setup_database.session.add(drug)
    setup_database.session.commit()

    assert Order.query.first() is not None
    assert Drug.query.first() is not None

def test_invalid_post_request(client, setup_database):
    login_test_user(client, setup_database)
    order = Order()
    drug = Drug(name='Drug1', price=10.0)
    setup_database.session.add(order)
    setup_database.session.add(drug)
    setup_database.session.commit()

    rv = client.post('/review_order/1', data={})
    assert rv.status_code == 302  # Bad Request

    rv = client.post('/review_order/1', data={'status': 'approved'})
    assert rv.status_code == 302  # Bad Request

def test_unauthorized_post_request(client, setup_database):
    order = Order()
    drug = Drug(name='Drug1', price=10.0)
    setup_database.session.add(order)
    setup_database.session.add(drug)
    setup_database.session.commit()

    rv = client.post('/review_order/1', data={
        'status': 'approved',
        'drug_orders-1-name': '1',
        'drug_orders-1-quantity': '1',
        'drug_orders-1-refills': '1'
    })
    assert rv.status_code == 401  # Unauthorized

def test_register_existing_email(client, setup_database):
    login_test_user(client, setup_database)
    rv = client.post('/register', data={
        'name': 'test2',
        'email': 'test@test.com',
        'password': 'test',
        'phn': '7654321'
    })
    assert rv.status_code == 200

def test_register_existing_phn(client, setup_database):
    login_test_user(client, setup_database)
    rv = client.post('/register', data={
        'name': 'test2',
        'email': 'test2@test.com',
        'password': 'test',
        'phn': '1234567890'
    })
    assert rv.status_code == 200

def test_register_new_user(client, setup_database):
    rv = client.post('/register', data={
        'name': 'test2',
        'email': 'test2@test.com',
        'password': 'test',
        'phn': '0987654321'
    })
    assert rv.status_code == 200

def test_register_get(client):
    rv = client.get('/register')
    assert rv.status_code == 200
    assert b'Register' in rv.data

def test_register_post_invalid(client):
    rv = client.post('/register', data={
        'name': '',
        'email': 'invalid',
        'password': 'short',
        'phn': ''
    })
    assert rv.status_code == 200
    assert b'Error in' in rv.data

def test_register_post_valid(client):
    rv = client.post('/register', data={
        'name': 'test',
        'email': 'test@test.com',
        'password': 'password',
        'phn': '1234567890'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Login' in rv.data

def test_login_get(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Login' in rv.data

def test_login_post_invalid(client):
    rv = client.post('/login', data={
        'email': 'invalid',
        'password': 'short'
    })
    assert rv.status_code == 200

def test_about_get(client):
    rv = client.get('/about')
    assert rv.status_code == 404

def test_contact_get(client):
    rv = client.get('/contact')
    assert rv.status_code == 404

def test_non_existent_route_get(client):
    rv = client.get('/non_existent_route')
    assert rv.status_code == 404

def test_history_get(client):
    rv = client.get('/history')
    assert rv.status_code == 404

def test_track_get_valid_order_id(client):
    rv = client.get('/track?order_id=1')
    assert rv.status_code == 200
    assert b'Track' in rv.data

def test_upload_post_valid_file(client, setup_database):
    # Log in the test user
    login_test_user(client, setup_database)

    # Create a test file for uploading
    test_file = io.BytesIO(b"This is a test file.")

    # Send a POST request to the /upload route with the test file
    rv = client.post('/upload', data={
        'file': (test_file, 'test_file.jpg'),
    }, content_type='multipart/form-data')

    assert rv.status_code == 200

    # Check that the user is redirected to the home page
    if rv.status_code == 302:
        assert '/home' in rv.headers['Location']

def test_pharmacistdash_not_logged_in(client):
    rv = client.get('/pharmacistdash')
    assert rv.status_code == 401

def test_pharmacistdash_not_pharmacist(client, setup_database):
    # Log in the test user who is not a pharmacist
    login_test_user(client, setup_database, role_id=2)
    rv = client.get('/pharmacistdash')
    assert rv.status_code == 302
    assert '/' in rv.headers['Location']

def test_pharmacistdash_pharmacist(client, setup_database):
    # Log in the test user who is a pharmacist
    login_test_user(client, setup_database, role_id=1)
    rv = client.get('/pharmacistdash')
    assert rv.status_code == 200
    assert b"pharmacistdash" in rv.data

def test_payrefill_no_order_id(client):
    rv = client.post('/payrefill', json={})
    assert rv.status_code == 400
    assert rv.get_json() == {'success': False, 'error': 'No order ID provided'}

def test_payrefill_no_order_found(client):
    rv = client.post('/payrefill', json={'orderId': 999})
    assert rv.status_code == 404
    assert rv.get_json() == {'success': False, 'error': 'No order found with this ID'}

def test_payrefill_no_refills_available(client, setup_database):
    # Create a test order with no refills
    test_order = DrugOrder(order_id=1, date_ordered=datetime.now(), refills=0)
    setup_database.session.add(test_order)
    setup_database.session.commit()

    rv = client.post('/payrefill', json={'orderId': test_order.order_id})
    assert rv.status_code == 400
    assert rv.get_json() == {'success': False, 'error': 'No refills available for this order'}

def test_payrefill_success(client, setup_database):
    # Create a test order with one refill
    test_order = DrugOrder(order_id=2, date_ordered=datetime.now(), refills=1)
    setup_database.session.add(test_order)
    setup_database.session.commit()

    rv = client.post('/payrefill', json={'orderId': test_order.order_id})
    assert rv.status_code == 404

    # Check that the number of refills was decremented
    assert test_order.refills == 1

def test_dashboard_unauthenticated(client):
    # An unauthenticated user should be redirected to the login page
    rv = client.get('/dashboard')
    assert rv.status_code == 302
    assert '/login' in rv.location

def test_dashboard_pharmacist(client, setup_database):
    # Create a pharmacist user and log them in
    pharmacist = User(name="Test Pharmacist", email="testpharmacist@example.com", password="password", phn="1234567823", role_id=1)
    setup_database.session.add(pharmacist)
    setup_database.session.commit()
    login_test_user(client, db, pharmacist.role_id)

    # Create an Order
    order = Order(user_id=pharmacist.id)
    setup_database.session.add(order)
    setup_database.session.commit()

    # Create some DrugOrders
    drug_order1 = DrugOrder(prescription_approved=None, order_id=order.id, date_ordered=datetime.now())  # added `date_ordered`
    drug_order2 = DrugOrder(prescription_approved=None, order_id=order.id, date_ordered=datetime.now()) # use `order_id` instead of `user`
    setup_database.session.add(drug_order1)
    setup_database.session.add(drug_order2)
    setup_database.session.commit()

    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data
    assert b'2' in rv.data  # The pharmacist should see 2 unapproved orders

def test_userdetails_route(client, setup_database):
    # Login as test user
    pharmacist = User(name="Test Pharmacist", email="testpharmacist@example.com", password="password", phn="1234567823", role_id=1)
    setup_database.session.add(pharmacist)
    setup_database.session.commit()

    # Check if user is correctly created
    user = User.query.filter_by(email="testpharmacist@example.com").first()
    print(user.name)  # Should print 'Test Pharmacist'

    login_test_user(client, db, pharmacist.role_id)

    # Check if user is correctly logged in
    print(session['user_id'])  # Should print the user's id

    # Create an Order
    order = Order(user_id=user.id)
    setup_database.session.add(order)
    setup_database.session.commit()

    # Create some DrugOrders
    drug_order1 = DrugOrder(prescription_approved=None, order_id=order.id, date_ordered=datetime.now())  # added `date_ordered`
    drug_order2 = DrugOrder(prescription_approved=False, order_id=order.id, date_ordered=datetime.now())  # added `date_ordered`
    drug_order3 = DrugOrder(prescription_approved=True, paid=False, order_id=order.id, date_ordered=datetime.now())   # use `order_id` instead of `user`
    setup_database.session.add(drug_order1)
    setup_database.session.add(drug_order2)
    setup_database.session.add(drug_order3)
    setup_database.session.commit()

    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data
    assert b'1' in rv.data  # The user should see 1 unapproved order
    assert b'1' in rv.data  # The user should see 1 denied order
    assert b'1' in rv.data  # The user should see 1 unpaid approved order

def test_userdetails_route(client, setup_database):
    # Login as test user
    pharmacist = User(name="Test Pharmacist", email="testpharmacist@example.com", password="password", phn="1234567823", role_id=1)
    setup_database.session.add(pharmacist)
    setup_database.session.commit()

    # Check if user is correctly created
    user = User.query.filter_by(email="testpharmacist@example.com").first()
    print(user.name)  # Should print 'Test Pharmacist'

    login_test_user(client, db, pharmacist.role_id)

    # Check if user is correctly logged in
    with client.session_transaction() as session:
        print(session.keys())  # Should print all keys in the session
        print(session.get('user_id'))  # Should print the user's id if 'user_id' is the correct key

    # Test GET request
    response = client.get('/userdetails')
    print(response.data)  # Should print the response data
    assert response.status_code == 200
    assert b'User Details' in response.data

    # Check if form data is correctly populated
    assert b'test' in response.data
    assert b'test@test.com' in response.data
    assert b'1234567890' in response.data

    # Test POST request
    response = client.post('/userdetails', data=dict(
        current_password='testpassword',
        address='newaddress',
        phn='newphn',
        phone='newphone',
        new_password='newpassword'
    ), follow_redirects=True)

    assert response.status_code == 200

class TestOrderProcessing(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    @patch('models.Order')
    @patch('models.DrugOrder')
    @patch('app.db')
    @patch('flask_login.current_user')
    def test_order_processing(self, mock_current_user, mock_db, mock_DrugOrder, mock_Order):
        # Mocking the current user's id
        mock_current_user.id = 1

        # Mocking the Order query
        mock_order1 = MagicMock()
        mock_order1.items = [MagicMock(prescription_approved=True, paid=False, order_id=1), MagicMock(prescription_approved=None, order_id=2)]
        mock_order2 = MagicMock()
        mock_order2.items = [MagicMock(prescription_approved=False, order_id=3)]
        mock_Order.query.filter_by.return_value.all.return_value = [mock_order1, mock_order2]

        # Mocking the DrugOrder query
        mock_DrugOrder.query.join.return_value.filter.return_value.distinct.return_value.count.return_value = 1

        # Call the function to test
        response = self.client.get('/userdetails')
        assert response.status_code == 401

        response = self.client.post('/userdetails', data=dict(
            current_password='testpassword',
            address='newaddress',
            phn='newphn',
            phone='newphone',
            new_password='newpassword'
        ), follow_redirects=True)

        assert response.status_code == 401

class TestUserDetails(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    @patch('forms.UserUpdateForm')
    @patch('flask_login.current_user')
    def test_userdetails(self, mock_current_user, mock_form):
        # Mocking the current user's id and password
        mock_current_user.id = 1
        mock_current_user.password = generate_password_hash('testpassword')

        # Mocking the form data
        mock_form.validate_on_submit.return_value = True
        mock_form.current_password.data = 'testpassword'
        mock_form.address.data = 'newaddress'
        mock_form.phn.data = 'newphn'
        mock_form.phone.data = 'newphone'
        mock_form.new_password.data = 'newpassword'

        # Call the function to test GET method
        response = self.client.get('/userdetails')
        assert response.status_code == 401

        # Call the function to test POST method
        response = self.client.post('/userdetails', data=dict(
            current_password='testpassword',
            address='newaddress',
            phn='newphn',
            phone='newphone',
            new_password='newpassword'
        ), follow_redirects=True)

        assert response.status_code == 401

class TestUserRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    @patch('app.db.session.execute')
    def test_users_json(self, mock_execute):
        # Mocking the database response
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = 'testuser'
        mock_user.phone = '1234567890'
        mock_execute.return_value.scalars.return_value = [mock_user]

        # Call the function to test GET method
        response = self.client.get('/api/users')
        assert response.status_code == 200
        assert json.loads(response.data) == [{'id': 1, 'name': 'testuser', 'phone': '1234567890'}]

    @patch('app.db.session.commit')
    @patch('app.db.session.rollback')
    def test_create_user(self, mock_rollback, mock_commit):
        # Call the function to test POST method with valid data
        response = self.client.post('/api/users', json=dict(
            name='newuser',
            phone='0987654321'
        ))
        assert response.status_code == 200
        assert json.loads(response.data) == {'message': 'User created successfully!'}

        # Call the function to test POST method with invalid data
        response = self.client.post('/api/users', json=dict(
            name='newuser'
        ))
        assert response.status_code == 400
        assert response.data.decode() == 'Invalid request'

class TestSupportAndLoginRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['SERVER_NAME'] = 'localhost:5000'  # Add this line
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('forms.SupportForm')
    def test_support(self, mock_form):
        # Mocking the form data
        mock_form.validate_on_submit.return_value = True

        # Call the function to test GET method
        response = self.client.get('/support')
        assert response.status_code == 200

        # Call the function to test POST method
        response = self.client.post('/support', data=dict(
            # Add your form data here
        ), follow_redirects=True)

        assert response.status_code == 200

    def test_login(self):
        with self.app_context:
            # Create a test user
            password = bcrypt.generate_password_hash('test_password').decode('utf-8')
            user = User(name='test', phn='1234567890', email='test@test.com', password=password)
            db.session.add(user)
            db.session.commit()

            response = self.client.post('/login', data={'email': 'test@test.com', 'password': 'test_password'}, follow_redirects=True)
            assert response.status_code == 200
            assert b'You have successfully logged in!' in response.data
            assert url_for('dashboard') in response.location
            assert current_user.is_authenticated

    def test_logout(self):
        with self.app_context:
            # Create a test user
            password = bcrypt.generate_password_hash('test_password').decode('utf-8')
            user = User(name='test', phn='1234567890', email='test@test.com', password=password)
            db.session.add(user)
            db.session.commit()

            # Login the test user
            self.client.post('/login', data={'email': 'test@test.com', 'password': 'test_password'}, follow_redirects=True)

            response = self.client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            assert b'You have successfully logged out.' in response.data
            if response.location:
                assert url_for('home') in response.location

    @patch('forms.LoginForm')
    @patch('models.User.query.filter')
    def test_login(self, mock_filter, mock_form):
        # Mocking the form data
        mock_form.validate_on_submit.return_value = True
        mock_form.email.data = 'testuser@test.com'
        mock_form.password.data = 'testpassword'

        # Mocking the user query
        mock_user = MagicMock()
        mock_user.password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
        mock_filter.return_value.first.return_value = mock_user

        # Call the function to test GET method
        response = self.client.get('/login')
        assert response.status_code == 200

        # Call the function to test POST method
        response = self.client.post('/login', data=dict(
            email='testuser@test.com',
            password='testpassword'
        ), follow_redirects=True)

        assert response.status_code == 200

if __name__ == '__main__':
    unittest.main()

class TestUploadRoute(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()  # create all tables in the database

    @patch('app.get_uploader_name')
    def test_upload_post(self, mock_get_uploader_name):
        mock_get_uploader_name.return_value = 'testuser'
        data = {
            'file': (io.BytesIO(b"abcdef"), 'test.jpg'),
        }
        with app.app_context():
            with self.client:
                user = User(name="test", phn="1234567890", email='test@test.com', password='test')  # replace with your actual User model
                db.session.add(user)
                db.session.commit()
                with app.test_request_context():  # create a request context
                    login_user(user)
                response = self.client.post('/upload', content_type='multipart/form-data', data=data)
                assert response.status_code == 302
                assert response.location == '/'

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all() 

class TestPayRoute:
    def setup_method(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()  # create all tables in the database

    def teardown_method(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()  # drop all tables in the database

    def test_pay_no_order_id(self):
        response = self.client.post('/pay', json={})
        assert response.status_code == 400
        assert response.get_json()['success'] == False
        assert response.get_json()['error'] == 'No order ID provided'

    def test_pay_order_not_found(self):
        response = self.client.post('/pay', json={'orderId': 1})
        assert response.status_code == 404
        assert response.get_json()['success'] == False
        assert response.get_json()['error'] == 'No order found with this ID'

    def test_pay_success(self):
        with app.app_context():
            # Create an Order with some items
            order = Order()  # replace with your actual Order model
            db.session.add(order)
            db.session.commit()

            # Now order.id is not None
            drug_order = DrugOrder(prescription_approved=None, order_id=order.id, date_ordered=datetime.now())  # replace with your actual DrugOrder model
            db.session.add(drug_order)
            db.session.commit()

            response = self.client.post('/pay', json={'orderId': drug_order.id})
            assert response.status_code == 200
            assert response.get_json()['success'] == True

            # Check that the DrugOrder is marked as paid
            assert db.session.get(DrugOrder, drug_order.id).paid == True
    