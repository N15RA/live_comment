#!/bin/bash

export FLASK_APP=$1

flask db migrate
flask db upgrade