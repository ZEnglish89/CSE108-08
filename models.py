from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # plain text for lab
    role = db.Column(db.String(20), nullable=False)  # admin / teacher / student
#    classes = db.Column(db.JSON, nullable = True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(120),unique = True, nullable = False)
    Teacher = db.Column(db.String(120),nullable = False)
    Time = db.Column(db.String(120),nullable = False)
    currStudents = db.Column(db.Integer,nullable = False)
    maxStudents = db.Column(db.Integer,nullable = False)
    Students = db.Column(db.JSON,nullable = False)