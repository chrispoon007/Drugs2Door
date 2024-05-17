import pytest
from app import app, db
from models import Order, DrugOrder, Drug, User
from flask import url_for, Flask
from werkzeug.security import generate_password_hash
from flask_bcrypt import Bcrypt
from flask_login import login_user

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

def login_test_user(client, setup_database):
    hashed_password = bcrypt.generate_password_hash('test').decode('utf-8')
    test_user = User(name='test', email='test@test.com', password=hashed_password, phn='1234567890', role_id=1)
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