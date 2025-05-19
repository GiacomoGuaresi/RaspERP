from flask_login import UserMixin
from app.database import get_db

class User(UserMixin):
    def __init__(self, username, email, password):
        self.id = username
        self.email = email
        self.password = password

    @staticmethod
    def get_by_email(email):
        db = get_db()
        cur = db.execute('SELECT Username, Email, Password FROM User WHERE Email = ?', (email,))
        row = cur.fetchone()
        if row:
            return User(row['Username'], row['Email'], row['Password'])
        return None

    def load_user(user_id):
        db = get_db()
        cur = db.execute('SELECT Username, Email, Password FROM User WHERE Username = ?', (user_id,))
        row = cur.fetchone()
        if row:
            return User(row['Username'], row['Email'], row['Password'])
        return None

    def update(self):
        db = get_db()
        db.execute('UPDATE User SET Email = ?, Password = ? WHERE Username = ?', (self.email, self.password, self.id))
        db.commit()

    def get_by_pin(pin):
        db = get_db()
        cur = db.execute('SELECT Username, Email, Password FROM User WHERE Pin = ?', (pin,))
        row = cur.fetchone()
        if row:
            return User(row['Username'], row['Email'], row['Password'])
        return None