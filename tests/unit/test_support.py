import pytest
from Drugs2Door.app import support

def format_first_name(first_name):
    if first_name is None:
        raise TypeError("First name cannot be empty!")
    return first_name

def test_format_first_name():
    assert format_first_name('John') == 'John'
    assert format_first_name('John') != 'john'
    with pytest.raises(TypeError):
        format_first_name(None)

def format_last_name(last_name):
    if last_name is None:
        raise TypeError("Last name cannot be empty!") 
    return last_name

def test_format_last_name():
    assert format_last_name('Doe') == 'Doe'
    assert format_last_name('Doe') != 'doe'
    with pytest.raises(TypeError):
        format_last_name(None)

def format_email(email):
    if email is None:
        raise TypeError("Email cannot be empty!")
    if '@' not in email:
        raise ValueError("Invalid email address")
    return email
