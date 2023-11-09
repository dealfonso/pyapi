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
from datetime import datetime
from . import config

def _n_debug_val(name):
    try:
        return [ "OUTPUT", "FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE" ].index(name.upper())
    except:
        p_log("ERROR", f"Invalid log level: {name}; fallback to INFO")
        return _n_debug_val("INFO")

def p_log(level, *args):
    if _n_debug_val(level) <= _n_debug_val(config.LOG_LEVEL):
        log_string = "[{}] {} {}".format(level, str(datetime.now()), " ".join([str(x) for x in args]))
        if config.LOG_FILE is not None:
            try:
                with open(config.LOG_FILE, "a") as f:
                    f.write(log_string + "\n")
                    f.flush()
            except Exception as e:
                print("Error writting to log file %s: %s" % (config.LOG_FILE, str(e)))
                print("Deactivating writting to log file")
                config.LOG_FILE = None

        if not config.QUIET:
            print(log_string)

def p_trace(*args):
    p_log("TRACE", *args)

def p_debug(*args):
    p_log("DEBUG", *args)

def p_info(*args):
    p_log("INFO", *args)

def p_warning(*args):
    p_log("WARN", *args)

def p_error(*args):
    p_log("ERROR", *args)

def p_fatal(*args):
    p_log("FATAL", *args)
    sys.exit(1)

def p_output(*args):
    """This is a special log level that is always printed, regardless of the log level configuration
        (*) this is dedicated somehow to the output of the server, so it is not used in the rest of the code
    """
    p_log("OUTPUT", *args)