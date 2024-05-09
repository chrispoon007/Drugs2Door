from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length, Regexp, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phn = StringField('Personal Health Number (PHN)', validators=[DataRequired(), Length(min=10, max=10), Regexp('^[0-9]*$', message="PHN must contain only numbers")])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class UserUpdateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'readonly': True})
    name = StringField('Name', validators=[Optional(), Length(min=2, max=50)], render_kw={'readonly': True}) 
    address = TextAreaField('Address', validators=[Optional(), Length(min=0, max=255)])  
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=10), Regexp('^[0-9]*$', message="Phone number must contain only numbers")]) 
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])  
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])  
    submit = SubmitField('Update')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
