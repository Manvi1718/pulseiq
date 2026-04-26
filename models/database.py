from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ─── USER TABLE ───────────────────────────────────────────────


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One user can have many cases
    cases = db.relationship('Case', backref='user', lazy=True,
                            cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# ─── CASE TABLE ───────────────────────────────────────────────
class Case(db.Model):
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(50), default='Facebook')
    keyword = db.Column(db.String(200), nullable=False)
    time_range = db.Column(db.String(50), default='Last 7 days')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One case can have many posts
    posts = db.relationship('Post', backref='case', lazy=True,
                            cascade='all, delete-orphan')

    @property
    def post_count(self):
        return len(self.posts)

    def __repr__(self):
        return f'<Case {self.name}>'


# ─── POST TABLE ───────────────────────────────────────────────
class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    post_id = db.Column(db.String(200))
    text = db.Column(db.Text)
    author = db.Column(db.String(200))
    likes = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    platform = db.Column(db.String(50))
    post_url = db.Column(db.String(500))
    posted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_json = db.Column(db.Text)  # Full raw Apify response stored here

    def __repr__(self):
        return f'<Post {self.post_id}>'
