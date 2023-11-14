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
from .debug import *
import logging
import traceback

def run(api, *, host: str = "0.0.0.0", port: int = 8000, log_level: str = "info", log_api_calls = False, log_uvicorn = True):
    """
    Starts uvicorn with the given API, integrating uvicorn with the logging system of this library

    Args:
        api (FastAPI): The API to start
        host (str, optional): the ip address in which to listen. Defaults to "0.0.0.0".
        port (int, optional): the port in which to listen. Defaults to 8000.
        log_level (str, optional): the log level to log. Defaults to "info".
        log_api_calls (bool, optional): whether to log the calls to the API or not in the log file. Defaults to False.
        log_uvicorn (bool, optional): if true, the uvicorn logs will be shown in the log file. Defaults to True.

    """

    from uvicorn.config import LOGGING_CONFIG
    import uvicorn
    from fastapi import FastAPI

    if not isinstance(api, FastAPI):
        raise Exception("The api parameter must be a FastAPI instance")

    # Now we are configuring uvicorn log system so that it uses our own log system
    #   The mechanism is very simple: we create a filter that will print the log message
    #   using our own log system and then we return False so that the message is not logged
    #   by uvicorn
    class LogFilter(logging.Filter):
        def __init__(self, name: str = "", log = True) -> None:
            super().__init__(name)
            self._log = log

        def filter(self, record):
            if self._log:
                message = record.getMessage()
                p_log(record.levelname, message)

                # If there is an exception (because it is handling it during the logs), we print it
                info = sys.exc_info()
                if info[2] is not None:
                    p_log(record.levelname, "".join(traceback.format_tb(info[2], -5)))
            return not log_uvicorn
        
    LOGGING_CONFIG["filters"] = {
        'filter_default': {
            '()': LogFilter
        },
        'filter_access': {
            '()': LogFilter,
            'log': log_api_calls
        }
    }

    LOGGING_CONFIG["handlers"]["default"]["filters"] = ["filter_default"]
    LOGGING_CONFIG["handlers"]["access"]["filters"] = ["filter_access"]

    uvicorn.run(api, host=host, port=port, log_config=LOGGING_CONFIG, log_level=log_level.lower())