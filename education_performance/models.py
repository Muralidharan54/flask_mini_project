
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='viewer')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class EducationData(db.Model):
    __tablename__ = 'education_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hours_studied = db.Column(db.Float)
    attendance = db.Column(db.Float)
    sleep_hours = db.Column(db.Float)
    physical_activity = db.Column(db.String(20))
    learning_disabilities = db.Column(db.String(20))
    parental_involvement = db.Column(db.String(20))
    parental_education_level = db.Column(db.String(50))
    distance_from_home = db.Column(db.String(20))
    peer_influence = db.Column(db.String(20))
    exam_score = db.Column(db.Float)

