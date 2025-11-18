from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Enrollment junction table for many-to-many relationship
enrollments = db.Table('enrollments',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('grade', db.Integer, default=0)  # Store grade as percentage
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    enrolled_courses = db.relationship('Course', secondary=enrollments, backref=db.backref('enrolled_students'))

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=True, nullable=False)
    teacher = db.Column(db.String(120), nullable=False)
    time = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)