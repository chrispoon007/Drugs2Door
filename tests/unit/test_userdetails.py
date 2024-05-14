import pytest

# Test the format_phone function
def format_phone(phone):
    if phone is None:
        raise TypeError("Phone number cannot be None")
    phone = phone.replace("-", "")
    return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]

# The following will test if the phone number will work with dashes or without dashes
def test_format_phone():
    assert format_phone('1234567890') == '123-456-7890'
    assert format_phone('123-456-7890') == '123-456-7890'
    assert format_phone('12345678') != '123-456-7890'
    assert format_phone('123-456-78901') != '123-456-7890'
# The following will test if it raises a type error if the phone number is not a string
    with pytest.raises(TypeError):
        format_phone(None)