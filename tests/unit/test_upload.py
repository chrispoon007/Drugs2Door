import pytest
from flask_testing import TestCase
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.datastructures import FileStorage
from Drugs2Door.app import app  # import the global app object
from forms import UploadForm

class TestUploadForm(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def test_upload_form(self):
    # Test with allowed file type
        with open('test.jpg', 'rb') as f:
            file_storage = FileStorage(f, filename='test.jpg')
            data = dict(
                file=file_storage,
                submit=True
            )
            form = UploadForm(data=data, formdata=None, csrf_enabled=False)
            print(form.data)  # print the form data
            if not form.validate():
                print(form.errors)
            assert form.validate() is True

        # Test with disallowed file type
        with open('test.txt', 'rb') as f:
            file_storage = FileStorage(f, filename='test.txt')
            data = dict(
                file=file_storage,
                submit=True
            )
            form = UploadForm(data=data, formdata=None, csrf_enabled=False)
            print(form.data)  # print the form data
            if not form.validate():
                print(form.errors)
            assert form.validate() is False

if __name__ == '__main__':
    pytest.main()