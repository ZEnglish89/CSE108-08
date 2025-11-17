from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')])
    submit = SubmitField('Submit')

class newCourse(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    teacher = StringField("Teacher",validators=[DataRequired()])
    time = StringField("Time", validators=[DataRequired()])
    maxStudents = StringField("Student Capacity", validators=[DataRequired()])
    submit = SubmitField("Submit")