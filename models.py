import datetime
import hashlib

from exts import db

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.SmallInteger, default=-1) # 0 for yt, 1 for slido
    name = db.Column(db.Text, nullable=False, default='Noname')
    icon = db.Column(db.Text, nullable=True)
    text = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime, default=datetime.datetime.now())

    stream_id = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<Comment {self.id} {self.name}>'

    def to_dict(self):
        return {
            'type': self.type,
            'name': self.name,
            'icon': self.icon,
            'text': self.text,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def to_md5(self):
        m = hashlib.md5()
        m.update(f'{self.id}{self.type}{self.name}{self.icon}{self.text}{self.time}'.encode('utf-8'))
        return m.hexdigest()

class CommentHash(db.Model):
    __tablename__ = 'comment_hash'

    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(32), nullable=False, unique=True)

    def __repr__(self):
        return f'<CommentHash {self.id} {self.hash}>'

class Token(db.Model):
    __tablename__ = 'token'

    id = db.Column(db.Integer, primary_key=True)
    credentials = db.Column(db.JSON)

    def __repr__(self):
        return f'<Token {self.id}>'
