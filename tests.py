import unittest
from datetime import datetime, timedelta

from app import db, create_app
from app.models import User, Equation
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_equation_stored(self):
        u = User(username='karl')
        now = datetime.utcnow()
        e1 = Equation(x_var=10, y_var=2, operator='*', author=u,
                      timestamp=now)
        e1.calculate()
        db.session.add(e1)
        e2 = Equation(x_var=10, y_var=2, operator='/', author=u,
                      timestamp=now)
        e2.calculate()
        db.session.add(e2)
        db.session.commit()
        equations = Equation.query.filter_by(user_id=u.id).all()
        self.assertEqual(equations, [e1, e2])

    def test_calculate(self):
        u = User(username='karl')
        now = datetime.utcnow()
        operators = ['+', '-', '*', '/']
        equations = []
        answers = [12, 8, 20, 5]
        for operator in operators:
            equation = Equation(x_var=10, y_var=2, operator=operator, author=u,
                                timestamp=now)
            equation.calculate()
            equations.append(equation.equation_result)
        equation_answers = list(zip(equations, answers))
        for test in equation_answers:
            self.assertEqual(test[0], test[1])

    def test_password_hashing(self):
        u = User(username='frank')
        u.set_password('karl')
        self.assertFalse(u.check_password('frank'))
        self.assertTrue(u.check_password('karl'))

    def test_avatar(self):
        u = User(username='pete', email='pete@nonexistantemail.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/a631cb11854bd6ed0fc90cafea4e3d31'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@nonexistantemail.com')
        u2 = User(username='rachel', email='rachel@nonexistantemail.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u2.followed.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'rachel')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_equations(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four equations
        now = datetime.utcnow()
        e1 = Equation(x_var=1, y_var=1, operator='+', author=u1,
                      timestamp=now + timedelta(seconds=1))
        e1.calculate()
        e2 = Equation(x_var=1, y_var=1, operator='-', author=u2,
                      timestamp=now + timedelta(seconds=1))
        e2.calculate()
        e3 = Equation(x_var=1, y_var=1, operator='*', author=u3,
                      timestamp=now + timedelta(seconds=1))
        e3.calculate()
        e4 = Equation(x_var=1, y_var=1, operator='/', author=u4,
                      timestamp=now + timedelta(seconds=1))
        e4.calculate()
        db.session.add_all([e1, e2, e3, e4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_equations().all()
        f2 = u2.followed_equations().all()
        f3 = u3.followed_equations().all()
        f4 = u4.followed_equations().all()
        self.assertCountEqual(f1, [e2, e4, e1])
        self.assertCountEqual(f2, [e2, e3])
        self.assertCountEqual(f3, [e3, e4])
        self.assertCountEqual(f4, [e4])


if __name__ == '__main__':
    unittest.main(verbosity=2)
