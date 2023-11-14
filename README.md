# PyAPI REST

This is a module that provides utilities to implement a REST API in Python. The utilities range from basic DB management to configuration management, including logging and easing the implementation of the REST calls.

## Features

- Includes an object to implement a DB that is backed in a json file
    - Needs to implement methods `_unserialize` (converts the content of the JSON file to internal structures) and `_serialize` (converts the internal structures to a serializable json object).
    - It implements _autosave_ features
- Implements configuration management
    - Easily load `yaml` files and put the values in a module or an object
- Implements logging
    - Log to a file and/or to the console
- Help to implement REST calls
    - Add the ability to use API keys
    - Help to implement authentication
    - It is based on [FastAPI](https://fastapi.tiangolo.com/).

## Installation

## Basic example

Here we include a full working example that covers a lot of the features of the module.

```python
parser = argparse.ArgumentParser(allow_abbrev=False)

parser.add_argument("-p", "--port", help="port in which to listen", default=None, type=int, dest="port")
parser.add_argument("-v", "--verbose", help="verbose", action="store_true", dest="verbose")
parser.add_argument("-i", "--ip", help="ip address in which to listen", default=None, type=str, dest="ip")
parser.add_argument("-c", "--config", help="configuration file", default=None, type=str, dest="config_file")
parser.add_argument("-q", "--quiet", help="suppress console output", action="store_true", dest="quiet")
parser.add_argument("-l", "--log-file", help="the log file", default=None, type=str, dest="log_file")

args = parser.parse_args()

# Create a config object
config = pyapi.config.Config(
    LOG_LEVEL="INFO",
    LOG_FILE=None,
    QUIET=False,
    PORT=8000,
    IP_ADDRESS="0.0.0.0"
)

# If a config file is supplied, use it as the first option
if args.config_file is not None:
    config.load(args.config_file, False)

# Override commandline options
if args.verbose:
    config.LOG_LEVEL = "DEBUG"

if args.log_file is not None:
    config.LOG_FILE = args.log_file

if args.quiet:
    config.QUIET = True

if args.port is not None:
    config.PORT = args.port

# Now we are going to configure the log system
pyapi.debug.set_log_file(config.LOG_FILE)
pyapi.debug.set_log_level(config.LOG_LEVEL)
pyapi.debug.set_quiet(config.QUIET)

p_debug(f"Now we are checking the IP address")
if args.ip is not None:
    import ipaddress
    try:
        ipaddress.ip_address(args.ip)
        config.IP_ADDRESS = args.ip
    except:
        p_fatal("Invalid IP address: %s" % args.ip)

p_debug(f"And now we start the server")

# Create the API
api = pyapi.fastapi.FastAPIX()

# Add the root endpoint (these are FastAPI things)
@api.get("/")
def home():
    return { "status": "OK", "message": "Hello world!" }

# Start the server according to the configuration
pyapi.uvicorn.run(api, host = config.IP_ADDRESS, port = config.PORT, log_level = config.LOG_LEVEL)
```

## Logging (`pyapi.debug`)

The module `pyapi.debug` provides different functions to log messages to the console and/or to a file. In particular, it provides the following functions: `p_debug`, `p_info`, `p_warning`, `p_error` and `p_fatal`.

### Configuring the log system

The log system can be configured by means of the following functions:

- `set_log_file`: Sets the log file. If `None` is passed, the log file is disabled.
- `set_log_level`: Sets the log level. The log level can be one of the following: `DEBUG`, `INFO`, `WARNING`, `ERROR` or `FATAL`.
- `set_quiet`: Sets the quiet mode. If `True` is passed, the console output is disabled.

## REST API (`pyapi.fastapi`)

This module exports a class named `FastAPIX` that extends the class `FastAPI` from the [FastAPI](https://fastapi.tiangolo.com/) module. The main difference is that it adds the ability to use API keys and to implement authentication, and some other facilities.

The signature of the constructor is the following:

```python
def __init__(self
    # Function to be called when the server starts
    on_start: Callable[[FastAPI], Any] = None, 
    # Function to be called when the server stops
    on_stop: Callable[[FastAPI], Any] = None,
    # List of API keys that are valid for this API
    api_keys : list[str] = None, 
    # Function to be called when a user is authenticated "def auth(username: str, password: str) -> str | bool"
    auth_user : Callable[[str, str], Union[str,bool]] = None,
    # The rest of the parameters are passed to the FastAPI constructor
    *args, **kwargs)
```

- `on_start`: A function that is called when the server starts. It receives the `FastAPI` object as parameter.
- `on_stop`: A function that is called when the server stops. It receives the `FastAPI` object as parameter.
- `api_keys`: A list of API keys that are valid for this API (they have to be passed in the `X-API-KEY` header or as `api-key` query var). If `None` is passed, no API keys are defined.
- `auth_user`: A function that is called when a user is authenticated. It receives the username and password as parameters and it has to return `True` if the user is authenticated or `False` otherwise.

### Other features

The class `FastAPIX` also provides the following features:
- Attach sub-APIs to the main API at a given path, using function `add_api(self, api: FastAPI, *, base_path = "/")`.
- Add a function that helps to obtain the username of the authenticated user that is using a route
    > In your routes you can add the parameter `username: Annotated[ str, Depends(api.get_username) ]` and it will contain the username of the authenticated user, or None (if no credentials were provided).

### Decorating the calls

The class `FastAPIX` provides the same route decorators that are provided by the `FastAPI` class, but adding some extra functionality. In particular, it offers the following decorators: `get`, `post`, `put`, `delete`, `patch`, `options`, `head` and `trace`, and they all accept the same parameters as the decorators of the `FastAPI` class, but also the next ones:

- `require_keys`: if `True` is passed, a valid API key is required to call the endpoint. The API key can be passed in the `X-API-KEY` header or as `api-key` query var, and it has to be one of the API keys defined in the constructor of the class.
- `require_auth`: if `True` is passed, the user has to be authenticated to call the endpoint. The authentication is done by calling the function passed in the constructor of the class. The function receives the username and password as parameters and it has to return `True` if the user is authenticated or `False` otherwise.
- `allow_anonymous`: if `True` is passed, the user does not need to be authenticated to call the endpoint. This parameter completes the `require_auth` parameter, so if both are `True`, the user does not need to be authenticated but the request has to include a username and a password.

As an example, the following code defines an endpoint that requires a valid API key and that the user is authenticated:

```python
@api.get("/test", require_keys=True, require_auth=True)
def test():
    return { "status": "OK", "message": "Hello world!" }
```

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

## `uvicorn` helper

This module exports a function named `run` that can be used to start a server. It is a wrapper around the `uvicorn.run` function, but it adds some extra functionality. In particular, it enables to mute the console output and to log to a file by integrating the logging system of `uvicorn` with the one of `pyapi.debug`.

The signature of the function is the following:

```python
def run(api, *, host: str = "0.0.0.0", port: int = 8000, log_level: str = "info", log_api_calls = False, log_uvicorn = True):
```

## Configuration management (`pyapi.config`)

The module `pyapi.config` provides different mechanisms to manage configuration variables:
- The `Config` class: A class that can be used to define configuration variables and load them from a configuration file.
- The `load` function: A function that can be used to load a configuration file and put the values in a module or an object.

### The `Config` class

The `Config` class can be used to define configuration variables and load them from a configuration file. There are different ways to use it:

#### Subclassing `Config` class

You can subclass the `Config` class and define your own variables:

```python
import pyapi.config

class MyConfig(pyapi.config.Config):
    IP_ADDRESS = "0.0.0.0"
    PORT = 8000
```

Then you can instantiate your class and use the variables defined there (well... we did not anything yet), but now you can load a configuration file and the values will be put in the variables:

```yaml
IP_ADDRESS: 127.0.0.1
```

```python
config = MyConfig()
config.load("myconfig.yaml")
print(config.IP_ADDRESS)
```

#### Using the `Config` class directly

If you do not want to subclass the `Config` class, you can use it directly:

```python
import pyapi.config

config = pyapi.config.Config(
    IP_ADDRESS="0.0.0.0",
    PORT=8000
)
```

This example is equivalent to the previous one, but now the variables are defined in the constructor of the class, along with the default values. And now you can load a configuration file and the values will be put in the variables:

```yaml
IP_ADDRESS: 127.0.0.1
```

```python
config.load("myconfig.yaml")
print(config.IP_ADDRESS)
```

### The `load` function

Appart from the `Config` class, module `pyapi.config` exports the function `load`, which can be used to load a configuration file and put the values in a module or an object.

The function has the following signature:

```python
def load(filenames: Union[str, list[str]], layered_configuration = False, *, configurable_variables: list[str] | None = None, current_config: Any = None, subkey: str = None) -> list[str]:
```

This function loads the configuration files passed as parameter and puts the values in the module or object passed as parameter `current_config`. And the thing is that `current_config` can be any type of object and so you can use it to load the configuration in a module or in an object.

#### Loading configuration in an object

If you want to load the configuration in an object, you can do it by passing the object as the parameter `current_config`:

> I find that, as we have the `Config` class, it is better to use it instead of using an arbitraty object.

```python
import pyapi.config

class MyConfig:
    IP_ADDRESS = "0.0.0.0"
    PORT = 8000
```

And now you can load a configuration file and the values will be put in the variables:

```yaml
IP_ADDRESS: 127.0.0.1
```

```python
config = MyConfig()
pyapi.config.load("myconfig.yaml", current_config=config)
print(config.IP_ADDRESS)
```

> The key difference is that the object is not a subclass of `Config` class, but it is a normal object.

#### Loading configuration in a module

I really like to have a module with the configuration variables, so that I can import it in any part of the code and use the variables defined there. And the `load` function can be used to load the configuration into that module.

If we have the following module named `myconfig.py`:

```python
import pyapi.config

IP_ADDRESS = "0.0.0.0"
PORT = 8000

def load(filename: str) -> bool:
    return pyapi.config.load(filename, current_config=sys.modules[__name__])
```

Now we can load a configuration file and the values will be put in the variables:

```yaml
ip_address: 127.0.0.1
```

```python
import myconfig

myconfig.load("myconfig.yaml")
print(myconfig.IP_ADDRESS)
```

And now you can import the module in any part of your code and use the variables defined there, in the same way.