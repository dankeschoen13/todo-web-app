from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, URL, Length, Optional, Email


# User creation and login

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=250)])
    email = StringField('Email', validators=[DataRequired(), Length(max=250)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    SUBMIT = SubmitField('Sign up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(max=250)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    SUBMIT = SubmitField('Sign in')

# User creation and login

class ListForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    SUBMIT = SubmitField('Submit')

class TaskForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired(), Length(max=1000)])
    due_date = DateTimeField('Due Date', validators=[DataRequired()])
    SUBMIT = SubmitField('Submit')