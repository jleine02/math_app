from datetime import datetime, time
from hashlib import md5

import jwt
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

# this table only contains foreign keys so it is not declared as a model class
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    equations = db.relationship('Equation', backref='author',
                                lazy='dynamic')  # one-to-many relationships defined on one side
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship('User', secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if self.is_following(user) is False:
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_equations(self):
        followed = Equation.query.join(
            followers, (followers.c.followed_id == Equation.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Equation.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Equation.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': (time() + expires_in)},
                          current_app.config['SECRET KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except jwt.exceptions:
            return
        return User.query.get(id)


class Equation(db.Model):
    __searchable__ = ['equation_result']
    id = db.Column(db.Integer, primary_key=True)
    x_var = db.Column(db.Float)
    y_var = db.Column(db.Float)
    operator = db.Column(db.String())
    equation_result = db.Column(db.Float)
    equation_str = db.Column(db.String())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'''
            <Equation: {self.equation_str}>
            <x_var: {self.x_var}, operator: '{self.operator}', y_var: {self.y_var}, equation_result: {self.equation_result}>
            <timestamp: {self.timestamp}, user_id: {self.user_id}>'''

    def calculate(self):
        if self.operator == '+':
            self.equation_result = self.x_var + self.y_var
        elif self.operator == '-':
            self.equation_result = self.x_var - self.y_var
        elif self.operator == '*':
            self.equation_result = self.x_var * self.y_var
        elif self.operator == '/':
            self.equation_result = self.x_var / self.y_var

        self.equation_str = f'{self.x_var:,.2f} {self.operator} {self.y_var:,.2f} = {self.equation_result:,.2f}'

