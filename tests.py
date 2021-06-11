from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Equation


class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

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

    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Equation(equation_body="10 * 10 = 100", author=u1,
                      timestamp=now + timedelta(seconds=1))
        p2 = Equation(equation_body="5 + 5 = 10", author=u2,
                      timestamp=now + timedelta(seconds=4))
        p3 = Equation(equation_body="1 + 1 = 2", author=u3,
                      timestamp=now + timedelta(seconds=3))
        p4 = Equation(equation_body="50 / 5 = 10", author=u4,
                      timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
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
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])


if __name__ == '__main__':
    unittest.main(verbosity=2)
