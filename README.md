# PyAPI REST

This is a template project to ease the creation of applications that offer a REST API in Python

## Features

The skeleton includes some additional features:

- Includes an object to implement a DB that is backed in a json file
    - Needs to implement methods `_unserialize` (converts the content of the JSON file to internal structures) and `_serialize` (converts the internal structures to a serializable json object).
    - It implements _autosave_ features
- Implements configuration management
    - Those variables included in the `config` module can be set by means of using `yaml` files

## Workflow

1. Clone this repo

    ```bash
    $ git clone https://github.com/dealfonso/pyapi
    ```

1. Create a virtual environment and activate it

    ```bash
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    ```

1. Install the requirements

    ```bash
    $ pip install -r requirements.txt
    ```

1. Rename `pyapi` folder to the short name of your project.

1. Adjust the file `version.py` to meet the short name of your project
    > It will be used for the name of the expected configuration files and the default DB filename.

1. Implement the internal structures for your DB by subclassing class `JsonDB` and implementing the methods `_serialize` and `unserialize`
    - `_serialize` receives an object that is the result of parsing the json file that backs the database (i.e. the result of `_unserialize`). And is intended to derive the internal values from those stored in the DB.
    - `_unserialize` generates an object that is going to be saved in a json file, using json format, to later be retrieved to recover the state of the DB. (This is the reciprocal function from `_serialize`).

    > If you do not need any data to be stored by this means, you can safely ignore this step and remove the line `db = EmptyJsonDB(autosave=True)` from the example file `api.py`.

1. Add the configuration options as variables, in file `config.py`.
    > Take var `IP_ADDRESS` as an example on how to do it. That variable can be set in the configuration files as `ip_address` using `yaml` format.

1. Implement the REST calls in file `api.py`

## Configuration files

The default files that are going to be used are, where `version.SHORTNAME` is the short name of your project (defined in the module `version`):

1. `{version.SHORTNAME}.conf`
1. `etc/{version.SHORTNAME}.conf`
1. `/etc/{version.SHORTNAME}.conf`
1. `/etc/{version.SHORTNAME}/{version.SHORTNAME}.conf`
1. `/usr/local/etc/{version.SHORTNAME}.conf`

If one of them is found, it is going to be used. If more than one is found, only the first one is going to be used.

The variables that can be set in these files are those defined (and exported) in the module `config`. 

e.g. `IP_ADDRESS` is defined in `config.py` and can be set in the configuration files as `ip_address` using `yaml` format:

```yaml
ip_address: 127.0.0.1
```

The current version considers the following variables:

- `IP_ADDRESS`: The IP address in which the server will listen (the default is 0.0.0.0)
- `PORT`: The port in which the server will listen (the default is 8000)
- `DATABASE_FILE`: The file in which the database is stored (the default is `{version.SHORTNAME}.json`)
- `APIBASE`: The base URL of the server, just in case we want to use a different one (e.g. v1, v2, etc.) (the default is "")
- `API_KEYS`: The API keys to use for the API (if the list is empty, no API key is required); otherwise, the API key must be provided in the headers of the request using the key X-API-KEY or in the query string using the key api_key
- `AUTHORIZED_USERS`: The list of users that are authorized to use the API (if the list is empty, any user is authorized). The authentication is `HTTP-Basic`, but the passwords are not checked at this time.
    > It you want to implement authorization, please check function `get_current_username` at file `dependencies.py`
- `ALLOW_ANONYMOUS_USER`: If any user is authorized to use the API, this flag indicates whether anonymous users are allowed to use the API (i.e. requests in which the username is empty)
- `LOG_FILE`: The log file (if None, no log file is used). Defaults to `/var/log/{version.SHORTNAME}.log`
- `LOG_LEVEL`: The log level (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to `INFO`
- `QUIET`: Whether to suppress console output or not. Defaults to `False`
- `LOG_API_CALLS`: Whether to log the accesses to the API or not. Defaults to `True`
- `MUTE_UVICORN_LOGS`: Whether to mute the logs shown by uvicorn or not. Defaults to `True`

> You can check the different options and add your variables in the file `config.py`

Then you can use these variables in any part of the code by importing the module `config` and using the variables defined there:

```python
from pyapi import config

print(config.IP_ADDRESS)
```

> The `config` module also exports the function `load`, which can be used to load a configuration file. That is the function that is used in `__main__.py` to load the configuration file.

## `JsonDB` class

This is a class that does nothing but to provide a DB that is backed in a json file.

The underlying idea is to abstract the DB from the application, so that the application does not need to know how the DB is implemented. So in this class you should implement your mechanisms to retrieve the data structures in the application so that if you want to upgrade the DB to a different DB runtime, it would help you to do it.

e.g.

```python
class MyDB(JsonDB):
    tokens = {}

    def _serialize(self, data):
        return self.tokens

    def _unserialize(self, data):
        self.tokens = data
        return true

    def getToken(self, tokenId):
        if tokenId in self.tokens:
            return self.tokens[tokenId]
        return None
```

In this way, the application can use the DB by means of using the method `getToken` without knowing how the DB is implemented.

## Running the application

From the root folder of the project, run:

```bash
$ python -m pyapi
```

You can pass some arguments to the application. The template considers the following ones:

- `--config`: Path to the configuration file to be used
- `--ip`: IP address in which to listen
- `--port`: Port in which to listen
- `--database-file`: Path to the DB file to be used
- `--log-file`: Path to the log file to be used
- `--no-run`: Do not run the server (used to check the configuration file)
- `--quiet`: Suppress console output
- `--verbose`: Verbose output
- `--verbose-more`: Verbose more output

> You can check the different options in the file `pyapi/__main__.py`