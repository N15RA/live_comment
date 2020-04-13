import os

DEBUG = True
SESSION_PROTECTION = 'strong'
SECRET_KEY = os.urandom(128)

DIALECT = 'sqlite'
PATH = 'data.db'

DB_URI = "{}:///{}".format(DIALECT, PATH)
SQLALCHEMY_DATABASE_URI = "{}:///{}".format(DIALECT, PATH)
SQLALCHEMY_TRACK_MODIFICATIONS = False