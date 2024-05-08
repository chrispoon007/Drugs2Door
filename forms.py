from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length, Regexp

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phn = StringField('Personal Health Number (PHN)', validators=[DataRequired(), Length(min=10, max=10), Regexp('^[0-9]*$', message="PHN must contain only numbers")])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserUpdateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[Optional(), Length(min=0, max=50)])  # Optional name field
    address = TextAreaField('Address', validators=[Optional(), Length(min=0, max=255)])  # Optional address field
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=10), Regexp('^[0-9]*$', message="Phone number must contain only numbers")])  # Optional phone field with validation
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])  # Optional new password field
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])  # Confirm new password if provided
    submit = SubmitField('Update')