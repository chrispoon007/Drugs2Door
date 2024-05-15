from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length, Regexp, ValidationError
from models import User
from flask_wtf.file import FileField, FileRequired, FileAllowed

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phn = StringField('PHN', validators=[DataRequired(), Length(min=10, max=10), Regexp('^[0-9]*$', message="PHN must contain only numbers")])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class UserUpdateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'readonly': True})
    name = StringField('Name', validators=[Optional(), Length(min=2, max=50)], render_kw={'readonly': True}) 
    address = TextAreaField('Address', validators=[Optional(), Length(min=0, max=255)])  
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=12), Regexp('^[0-9]{3}-?[0-9]{3}-?[0-9]{4}$', message="Phone number must be in the format: 123-456-7890 or 1234567890")])
    phn = StringField('Personal Health Number', render_kw={'readonly': True})
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])  
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
