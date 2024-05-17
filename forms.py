from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, FormField, FieldList, BooleanField, HiddenField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length, Regexp, ValidationError
from models import User
from flask_wtf.file import FileField, FileRequired, FileAllowed

def password_complexity(form, field):
    password = field.data
    if password:  # Only check complexity if a password is provided
        if len(password) < 6 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or not any(not char.isalnum() for char in password):
            raise ValidationError("Password must be at least 6 characters long, contain a number, a letter, and a symbol.")

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phn = StringField('PHN', validators=[DataRequired(), Length(min=10, max=10), Regexp('^[0-9]*$', message="PHN must contain only numbers")])
    password = PasswordField('Password', validators=[DataRequired(), password_complexity])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class UserUpdateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'readonly': True})
    name = StringField('Name', validators=[Optional(), Length(min=2, max=50)], render_kw={'readonly': True}) 
    address = TextAreaField('Address', validators=[Optional(), Length(min=0, max=255)])  
    phone = StringField('Phone Number', validators=[Length(min=10, max=12), Regexp('^[0-9]{3}-?[0-9]{3}-?[0-9]{4}$', message="Phone number must be in the format: 123-456-7890 or 1234567890")])
    phn = StringField('Personal Health Number', render_kw={'readonly': True})
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[password_complexity])  
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])  
    submit = SubmitField('Update')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'bmp', 'pdf'], 'Images and PDFs only!')
    ])
    submit = SubmitField('Upload')

class SupportForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('E-mail Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Regexp(r'^\d{1,10}$', message="Phone number should be digits and up to 10 digits only")])
    message = TextAreaField('Message', validators=[Optional()])
    submit = SubmitField('Submit')

