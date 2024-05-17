import pytest
from unittest.mock import patch, mock_open
from manage import import_data
from models import Role, User

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



