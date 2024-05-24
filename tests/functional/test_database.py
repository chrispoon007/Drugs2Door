import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pathlib import Path
from models import User, Role, Drug, Order, DrugOrder
from db import db
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sql.db"
app.instance_path = Path("./data").resolve()
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)
bcrypt = Bcrypt(app)

@pytest.fixture
def client():
    app_context = app.app_context()
    app_context.push()
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()
    app_context.pop()

def test_user_model(client):
    role = Role(name='test_role')
    db.session.add(role)
    db.session.commit()

    user = User(name='test_user', email='test@test.com', password='test_password', role_id=role.id, phn='1234567890')
    db.session.add(user)
    db.session.commit()

    retrieved_user = User.query.filter_by(name='test_user').first()
    assert retrieved_user is not None
    assert retrieved_user.email == 'test@test.com'
    assert retrieved_user.role_id == role.id

def test_order_model(client):
    user = User(name='test_user', email='test@test.com', password='test_password', phn='1234567890')
    db.session.add(user)
    db.session.commit()

    order = Order(user_id=user.id)
    db.session.add(order)
    db.session.commit()

    retrieved_order = Order.query.filter_by(user_id=user.id).first()
    assert retrieved_order is not None
    assert retrieved_order.user_id == user.id


def test_drug_order_model(client):
    user = User(name='test_user', email='test@test.com', password='test_password', phn='1234567890')
    db.session.add(user)
    db.session.commit()

    drug = Drug(name='test_drug', price=10.00)
    db.session.add(drug)
    db.session.commit()

    order = Order(user_id=user.id)
    db.session.add(order)
    db.session.commit()

    drug_order = DrugOrder(order_id=order.id, drug_id=drug.id, quantity=1, date_ordered=datetime.now())
    db.session.add(drug_order)
    db.session.commit()

    retrieved_drug_order = DrugOrder.query.filter_by(order_id=order.id).first()
    assert retrieved_drug_order is not None