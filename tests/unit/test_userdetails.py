import pytest
from app import format_phone
from app import UserUpdateForm
from wtforms.validators import ValidationError
from Drugs2Door.app import app


# The following will test if the phone number will work with dashes or without dashes
def test_format_phone():
    assert format_phone('1234567890') == '123-456-7890'
    assert format_phone('123-456-7890') == '123-456-7890'
    assert format_phone('12345678') != '123-456-7890'
    assert format_phone('123-456-78901') != '123-456-7890'
    # The following will test if it raises a type error if the phone number is not a string
    with pytest.raises(TypeError):
        format_phone(None)

def test_user_update_form():
    with app.app_context():
        data = dict(
            email='test@example.com',
            name='Test User',
            address='123 Test St',
            phone='123-456-7890',
            phn='1234567890',
            current_password='password',
            new_password='newpassword1!',
            confirm_password='newpassword1!'
        )
        form = UserUpdateForm(data=data)
        assert form.validate() is True

        # Test with invalid email
        data['email'] = 'invalid email'
        form = UserUpdateForm(data=data)
        assert form.validate() is False
        assert 'email' in form.errors  

        # Test with invalid phone number
        data['email'] = 'test@example.com'
        data['phone'] = 'invalid phone number'
        form = UserUpdateForm(data=data)
        assert form.validate() is False
        assert 'phone' in form.errors

        # Test with password mismatch
        data['phone'] = '123-456-7890'
        data['new_password'] = 'newpassword'
        data['confirm_password'] = 'differentpassword'
        form = UserUpdateForm(data=data)
        assert form.validate() is False
        assert 'confirm_password' in form.errors

        # Test with short new password
        data['new_password'] = 'short'
        data['confirm_password'] = 'short'
        form = UserUpdateForm(data=data)
        assert form.validate() is False
        assert 'new_password' in form.errors

        # Test with missing current password
        data['new_password'] = 'newpassword'
        data['confirm_password'] = 'newpassword'
        data['current_password'] = ''
        form = UserUpdateForm(data=data)
        assert form.validate() is False
        assert 'current_password' in form.errors