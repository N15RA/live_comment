from flask import Flask
# from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

from exts import db
import config

# csrf = CSRFProtect()

def create_app():
	# Init app
	app = Flask(__name__)
	app.config.from_object(config)
	# Init csrf
	# csrf.init_app(app)
	# Init cors
	CORS(app)
	# Init db
	db.init_app(app)
	return app

app = create_app()