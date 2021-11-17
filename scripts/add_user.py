import argparse
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+"/.."))

from sqlservice import SQLClient
import config

db = SQLClient(config=config.SQL_VARIABLES)

from models import User

from werkzeug.security import generate_password_hash

def add_user(username, password):
    user = User()
    user.username = username
    user.password = generate_password_hash(password)
    db.session.add(user)
    db.session.commit()
    print('Added')
    
def del_user(username):
    db.query(User).filter(User.username==username).delete()
    db.session.commit()
    print("Deleted")

parser = argparse.ArgumentParser(description="Add user")
subparser = parser.add_subparsers(title='subcommands', description='valid subcommands', help='sub-command help')

add_parser = subparser.add_parser('add')
add_parser.set_defaults(command='add') # https://coderedirect.com/questions/205072/argparse-identify-which-subparser-was-used
add_parser.add_argument('username', help='Username')
add_parser.add_argument('password', help='Password')

del_parser = subparser.add_parser('del')
del_parser.set_defaults(command='del')
del_parser.add_argument('username', help='Username')

if __name__ == '__main__':
    args = parser.parse_args()

    if args.command == 'add':
        add_user(args.username, args.password)
    elif args.command == 'del':
        del_user(args.username)

    print(db.query(User).all())