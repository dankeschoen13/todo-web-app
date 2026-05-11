from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Length, EqualTo


# User creation and login

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=250)])
    email = StringField('Email', validators=[DataRequired(), Length(max=250)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Sign up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(max=250)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    SUBMIT = SubmitField('Sign in')