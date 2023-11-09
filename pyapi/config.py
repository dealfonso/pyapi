#
#    Copyright 2023 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import sys
from .debug import *
from .version import SHORTNAME

# The IP address in which the server will listen
IP_ADDRESS = "0.0.0.0"

# The port in which the server will listen
PORT = 8000

# The file in which the database is stored
DATABASE_FILE = f"{SHORTNAME}.json"

# The base URL of the server, just in case we want to use a different one (e.g. v1, v2, etc.)
APIBASE = ""

# The API keys to use for the API (if the list is empty, no API key is required); otherwise, the API key must be provided
#   in the headers of the request using the key X-API-KEY or in the query string using the key api_key
API_KEYS = [ 
]

# The list of users that are authorized to use the API (if the list is empty, any user is authorized)
AUTHORIZED_USERS = [
]

# If any user is authorized to use the API, this flag indicates whether anonymous users are allowed to use the API (i.e. 
# requests in which the username is empty)
ALLOW_ANONYMOUS_USER = True

# The log file (if None, no log file is used)
LOG_FILE = f"/var/log/{SHORTNAME}.log"

# The log level (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Quiet mode (no output to stdout)
QUIET = False

# Whether to log the accesses to the API or not
LOG_API_CALLS = True

# Whether to mute the logs shown by uvicorn or not
MUTE_UVICORN_LOGS = True

def load(filename: str, configurable_variables: list[str] | None = None) -> bool:
    """Reads a yaml configuration file and sets the variables in the current module

    Args:
        filename (str): the filename to read
        configurable_variables (list[str], optional): the list of variables that can be configured. Defaults to [].

    Returns:
        bool: True if the file was read successfully, False otherwise
    """
    import yaml
    try:
        with open(filename, "r") as f:
            configuration = yaml.safe_load(f)
            current_module = sys.modules[__name__]
            if configurable_variables is None:
                configurable_variables = [variable_name for variable_name in dir(current_module) if not variable_name.startswith("_") and not callable(getattr(current_module, variable_name)) and not type(getattr(current_module, variable_name)) == type(sys) ]
                
            for variable_name in configurable_variables:
                yaml_variable_name = variable_name.lower()
                if yaml_variable_name in configuration:
                    current_module.__dict__[variable_name] = configuration[yaml_variable_name]

            return True
    except Exception as e:
        p_error("Error reading configuration file %s: %s" % (filename, str(e)))
        return False
