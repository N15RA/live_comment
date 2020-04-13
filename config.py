import os

DEBUG = True
SESSION_PROTECTION = 'strong'
SECRET_KEY = os.urandom(128)

DIALECT = 'sqlite'
PATH = 'C:\\Users\\roy4801-PC\\Desktop\\NISRA\\live_comment\\data.db'

DB_URI = "{}:///{}".format(DIALECT, PATH)
SQLALCHEMY_DATABASE_URI = "{}:///{}".format(DIALECT, PATH)
SQLALCHEMY_TRACK_MODIFICATIONS = False