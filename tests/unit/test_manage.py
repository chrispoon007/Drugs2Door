import pytest
from unittest.mock import patch, mock_open
from manage import import_data
from models import User, Role, Order, DrugOrder, Drug
import unittest
from app import app, db
from manage import create_random_orders, create_pharmacist
from unittest.mock import patch

# Mock data for the CSV files
mock_users_csv = """name,phone
John Doe,1234567890
Jane Doe,0987654321"""

mock_drugs_csv = """name,price
Drug1,10.0
Drug2,20.0"""

# Mock bcrypt.hashpw function to return a simple hashed password
def mock_hashpw(password, salt):
    return b"hashed_password"

@patch("manage.bcrypt.hashpw", side_effect=mock_hashpw)
@patch("manage.db.session")
@patch("builtins.open", new_callable=mock_open)
def test_import_data(mock_file, mock_db, mock_bcrypt):
    # Mock db.session.query().get() to return None
    mock_db.query.return_value.get.return_value = None

    mock_file.side_effect = [mock_open(read_data=mock_users_csv).return_value,
                             mock_open(read_data=mock_drugs_csv).return_value]
    import_data()

    # Check if the add method was called
    assert mock_db.add.called

    # Check if the changes were committed
    assert mock_db.commit.call_count == 2

class TestManageFunctions(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['SERVER_NAME'] = 'localhost:5000'
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def test_create_random_orders(self):
        # Mock the random functions
        with patch('manage.random.randint', side_effect=[3, 60, 30, 3, 50]), \
            patch('manage.random.choice', side_effect=[True, True, False]):

            # Call the function
            create_random_orders()

            # Check that the correct number of orders were created
            with app.app_context():
                users = User.query.join(Role).filter(Role.name != 'Pharmacist').all()
                for user in users:
                    orders = Order.query.filter_by(user_id=user.id).all()
                    self.assertEqual(len(orders), 3)

                    # Check that each order has the correct number of drugs
                    for order in orders:
                        drug_orders = DrugOrder.query.filter_by(order_id=order.id).all()
                        self.assertEqual(len(drug_orders), 3)

    def test_create_pharmacist(self):
        # Call the function
        create_pharmacist()

        # Check that a pharmacist was created
        with app.app_context():
            pharmacist = User.query.filter_by(email='HGruber@example.com').first()
            self.assertIsNotNone(pharmacist)
            self.assertEqual(pharmacist.name, 'Hans Gruber')
            self.assertEqual(pharmacist.role.name, 'Pharmacist')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()



