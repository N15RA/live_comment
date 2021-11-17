#!/bin/bash

FLASK_APP=

flask db init
flask db migrate
flask db upgrade