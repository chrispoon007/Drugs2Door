import pytest
from app import app, db
from models import Order, DrugOrder, Drug, User
from flask import url_for, Flask
from werkzeug.security import generate_password_hash
from flask_bcrypt import Bcrypt
from flask_login import login_user
from datetime import datetime, timezone
import io
import os
from sqlalchemy.orm import session

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