import pytest
from wtforms import Form, StringField
from wtforms.validators import ValidationError
from forms import password_complexity

class DummyForm(Form):
    password = StringField('Password', [password_complexity])

# Create DummyField and DummyForm classes
def test_password_complexity1():
    class DummyField:
        def __init__(self, data):
            self.data = data

    class DummyForm:
        pass

    form = DummyForm()
    field = DummyField('123')

    with pytest.raises(ValidationError):
        password_complexity(form, field)



def test_password_complexity_alpha():
    class DummyField:
        def __init__(self, data):
            self.data = data

    class DummyForm:
        pass

    form = DummyForm()
    field = DummyField('abcdef')

    with pytest.raises(ValidationError):
        password_complexity(form, field)

def test_password_complexity_alphanumeric():
    class DummyField:
        def __init__(self, data):
            self.data = data

    class DummyForm:
        pass

    form = DummyForm()
    field = DummyField('abcdef123')

    with pytest.raises(ValidationError):
        password_complexity(form, field)

def test_password_complexity_valid():
    class DummyField:
        def __init__(self, data):
            self.data = data

    class DummyForm:
        pass

    form = DummyForm()
    field = DummyField('abcdef123!')

    try:
        password_complexity(form, field)
    except ValidationError:
        pytest.fail("ValidationError was raised when it shouldn't have been")
