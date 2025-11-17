import os

class Config:
    SECRET_KEY = "supersecretkey123"   # replace later, but ok for now

    # Database lives in /instance/app.db
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False