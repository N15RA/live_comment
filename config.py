import os

#SERVER_NAME = 'c.nisra.net:8080'

DEBUG = True
SESSION_PROTECTION = 'strong'
SECRET_KEY = os.urandom(128)

DIALECT = 'sqlite'
PATH = 'data.db'

DB_URI = "{}:///{}".format(DIALECT, PATH)
SQL_DATABASE_URI = "{}:///{}".format(DIALECT, PATH)
# SQLALCHEMY_DATABASE_URI = "{}:///{}".format(DIALECT, PATH)
# SQLALCHEMY_TRACK_MODIFICATIONS = False

SQL_ISOLATION_LEVEL = 'SERIALIZABLE'
SQL_ECHO = False
SQL_ECHO_POOL = False
SQL_CONVERT_UNICODE = True
# SQL_POOL_SIZE = 5
# SQL_POOL_TIMEOUT = 30
# SQL_POOL_RECYCLE = 3600
# SQL_MAX_OVERFLOW = 10
SQL_AUTOCOMMIT = False
SQL_AUTOFLUSH = True
SQL_EXPIRE_ON_COMMIT = True

# HACK: this
local = dict(locals())
sql_vars = {}
for k, v in local.items():
    if 'SQL' in k:
        sql_vars[k] = v
del local
SQL_VARIABLES = sql_vars
