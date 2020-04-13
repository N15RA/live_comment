import datetime
import hashlib

from sqlalchemy import Column, types
from sqlalchemy import MetaData
from sqlservice import ModelBase, as_declarative, declarative_base

metadata = MetaData()

# @as_declarative(metadata=metadata)
# class Model(ModelBase):
#     pass

# Or using the declarative_base function...
Model = declarative_base(ModelBase, metadata=metadata)

class Comment(Model):
    __tablename__ = 'comment'
    id = Column(types.Integer, primary_key=True)
    type = Column(types.SmallInteger, default=-1) # 0 for yt, 1 for slido
    name = Column(types.Text, nullable=False, default='Noname')
    icon = Column(types.Text, nullable=True)
    text = Column(types.Text, nullable=True)
    time = Column(types.DateTime, default=datetime.datetime.now())

    stream_id = Column(types.String, nullable=False)

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

class CommentHash(Model):
    __tablename__ = 'comment_hash'

    id = Column(types.Integer, primary_key=True)
    hash = Column(types.String(32), nullable=False, unique=True)

    def __repr__(self):
        return f'<CommentHash {self.id} {self.hash}>'

class Token(Model):
    __tablename__ = 'token'

    id = Column(types.Integer, primary_key=True)
    credentials = Column(types.JSON)

    def __repr__(self):
        return f'<Token {self.id}>'
