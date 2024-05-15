import pytest

# Test a upload_file function
def upload_file(file):
    if file is None:
        raise TypeError("File cannot be None")
    return file

# the following will test if the file is the correct file type

def test_upload_file():
    assert upload_file('file.png') == 'file.png'
    assert upload_file('file.jpg') == 'file.jpg'
    assert upload_file('file.pdf') == 'file.pdf'
    assert upload_file('file.txt') != 'file.png'
    assert upload_file('file.txt') != 'file.jpg'
    assert upload_file('') != 'file.jpg'

# The following will test if it raises a type error if the file is not a string

    with pytest.raises(TypeError):
        upload_file(None)