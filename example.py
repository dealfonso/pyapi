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

from pyapi.debug import *
import pyapi.config
import pyapi.fastapi
import pyapi.uvicorn
import argparse

def main():
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

if __name__ == "__main__":
    main()
