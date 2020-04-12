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

* Run (For test only)

```
python broadcast.py
```
