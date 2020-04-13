# live comment

## Setup

* Dependencies

```bash
pip install virtualenv
virtualenv venv
source ./venv/bin/activate
pip install -r ./requirement.txt
```

* Download OAuth Client Token from [Google API Console](https://console.developers.google.com/apis)
    * Specify the `CLIENT_SECRETS_FILE` variable in `broadcast.py`

* Initialize the db

```bash
python ./manage.py db init
python ./manage.py db migrate
python ./manage.py db upgrade
```

* Run (For test only)

```
python broadcast.py
```
