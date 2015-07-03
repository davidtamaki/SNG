from sqlalchemy import Column, ForeignKey, DateTime, Float, BigInteger, Integer, String, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sngsql.database import Base


user_hashtag = Table('user_hashtag', Base.metadata,
    Column('hashtag_id', Integer, ForeignKey('hashtag.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False))

user_url = Table('user_url', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('url_id', Integer, ForeignKey('url.id'), nullable=False))

user_word = Table('user_word', Base.metadata,
    Column('word_id', Integer, ForeignKey('word.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False))

item_word = Table('item_word', Base.metadata,
    Column('item_id', Integer, ForeignKey('item.id'), nullable=False),
    Column('word_id', Integer, ForeignKey('word.id'), nullable=False))

item_hashtag = Table('item_hashtag', Base.metadata,
    Column('hashtag_id', Integer, ForeignKey('hashtag.id'), nullable=False),
    Column('item_id', Integer, ForeignKey('item.id'), nullable=False))


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    contestant = Column(String(300), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    message = Column(String(300), nullable=False)
    item_id = Column(String(100), nullable=False, unique=True)
    item_type = Column(String(100), nullable=False)
    item_url = Column(String(100), nullable=False)
    location = Column(String(100)) # only twitter
    date = Column(DateTime(timezone=False), nullable=False)
    source = Column(String(100), nullable=False)

    # sentiment info
    polarity = Column(Float, nullable=False)
    subjectivity = Column(Float, nullable=False)
    sentiment = Column(String(100), nullable=False)

    # ranking info
    comment_count = Column(BigInteger) # only intstagram
    favorite_count = Column(BigInteger, nullable=False)
    share_count = Column(BigInteger) # only twitter

    # full json dump (for ref)
    data = Column(Text, nullable=False)

    # relations to other tables
    words = relationship('Word', backref='item', secondary='item_word')
    hashtags = relationship('Hashtag', backref='item', secondary='item_hashtag')

    def __repr__(self):
        return '<Item {}>'.format(self.item_id)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    uid = Column(String(50), nullable=False, unique=True)
    screen_name = Column(String(100), nullable=False, unique=True)
    followers_count = Column(BigInteger, nullable=False)
    friends_count = Column(BigInteger) # only twitter
    statuses_count = Column(BigInteger, nullable=False)
    rank = Column(Float, nullable=False)

    words = relationship('Word', backref='user', secondary='user_word')
    hashtags = relationship('Hashtag', backref='user', secondary='user_hashtag')
    urls = relationship('Url', backref='user', secondary='user_url')
    followers = relationship('Follower')

    def __repr__(self):
        return '<User {}>'.format(self.uid)


class Hashtag(Base):
    __tablename__ = 'hashtag'
    id = Column(Integer, primary_key=True)
    hashtag = Column(String(200), nullable=False)

    def __repr(self):
        return '<Hashtag {}>'.format(self.hashtag)


class Word(Base):
    __tablename__ = 'word'
    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.word)


class Url(Base):
    __tablename__ = 'url'
    id = Column(Integer, primary_key=True)
    url = Column(String(200), nullable=False)

    def __repr(self):
        return '<URL {}>'.format(self.url)



# adjacency list for followers
class Follower(Base):
    __tablename__ = 'follower'
    id = Column(Integer, primary_key=True)
    #parent_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    #child_id = Column(Integer, nullable=False)
    parent_id = Column(String(50), ForeignKey('user.uid'), nullable=False)
    child_id = Column(String(50), nullable=False)

    def __repr__(self):
        return 'Follower(parent=%s, child=%s)' % (self.parent_id, self.child_id)


