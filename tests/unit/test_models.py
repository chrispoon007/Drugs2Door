import pytest
from models import Role, User, Drug, Order, DrugOrder
from datetime import datetime

def test_role_model():
    role = Role()
    role.id = 1
    role.name = "admin"

    assert role.id == 1
    assert role.name == "admin"

def test_user_model():
    user = User()
    user.id = 1
    user.name = "John Doe"
    user.email = "jdoe@example.com"
    user.password = "password"
    user.address = "123 Main St"
    user.phone = "1234567890"
    user.phn = "1234567890"
    user.role_id = 1

    assert user.id == 1
    assert user.name == "John Doe"
    assert user.email == "jdoe@example.com"
    assert user.password == "password"
    assert user.address == "123 Main St"
    assert user.phone == "1234567890"
    assert user.phn == "1234567890"
    assert user.role_id == 1

def test_drug_model():
    drug = Drug()
    drug.id = 1
    drug.name = "Drug1"
    drug.price = 10.0

    assert drug.id == 1
    assert drug.name == "Drug1"
    assert drug.price == 10.0

def test_order_model():
    order = Order()
    order.id = 1
    order.user_id = 1

    assert order.id == 1
    assert order.user_id == 1

def test_drug_order_model():
    drug_order = DrugOrder()
    drug_order.id = 1
    drug_order.order_id = 1
    drug_order.drug_id = 1
    drug_order.quantity = 1
    drug_order.date_ordered = datetime.now()
    drug_order.date_delivered = datetime.now()
    drug_order.prescription_approved = True
    drug_order.refills = 0
    drug_order.image_file = "image.jpg"
    drug_order.paid = True

    assert drug_order.id == 1
    assert drug_order.order_id == 1
    assert drug_order.drug_id == 1
    assert drug_order.quantity == 1
    assert isinstance(drug_order.date_ordered, datetime)
    assert isinstance(drug_order.date_delivered, datetime)
    assert drug_order.prescription_approved == True
    assert drug_order.refills == 0
    assert drug_order.image_file == "image.jpg"
    assert drug_order.paid == True